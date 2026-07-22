#include <iostream>
#include <string>
#include <cstring>
#include <chrono>
#include <thread>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

// Strict, hardware-aligned memory block structures
constexpr char SHM_REGION_NAME[] = "/intentos_memory_bridge";
constexpr size_t SHM_ARENA_SIZE = 1024; // Pre-allocated 1KB static memory boundary

#pragma pack(push, 1)
struct SharedIntentPacket {
    uint64_t timestamp_us;
    int32_t modality;
    float features[4];
    char action_token[32];
    float confidence;
};
#pragma pack(pop)

class IntentOSMemoryBridge {
private:
    int shm_fd;
    void* mapped_region;
    bool is_host;

public:
    IntentOSMemoryBridge(bool create_as_host = true) : is_host(create_as_host), shm_fd(-1), mapped_region(nullptr) {}

    bool initialize() {
        if (is_host) {
            // 1. Unlink any stale system memory segments to avoid port-like conflicts
            shm_unlink(SHM_REGION_NAME);
            
            // 2. Open a raw POSIX shared memory block descriptor with Read/Write execution privileges
            shm_fd = shm_open(SHM_REGION_NAME, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);
            if (shm_fd == -1) return false;

            // 3. Ftruncate strictly allocates the exact byte dimension blocks directly inside RAM blocks
            if (ftruncate(shm_fd, SHM_ARENA_SIZE) == -1) return false;
        } else {
            // Consumer Mode: Open up the existing raw memory partition created by the host process
            shm_fd = shm_open(SHM_REGION_NAME, O_RDWR, 0);
            if (shm_fd == -1) return false;
        }

        // 4. Map the raw file descriptor straight into this process's virtual address memory handles (mmap)
        mapped_region = mmap(nullptr, SHM_ARENA_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
        return mapped_region != MAP_FAILED;
    }

    void write_intent(const SharedIntentPacket& packet) {
        if (mapped_region) {
            // Zero-Copy Memory Write: Direct, byte-aligned copy straight into hardware RAM
            std::memcpy(mapped_region, &packet, sizeof(SharedIntentPacket));
        }
    }

    SharedIntentPacket read_intent() {
        SharedIntentPacket packet{};
        if (mapped_region) {
            // Zero-Copy Memory Read: Instantly mirror RAM state with near-zero latency
            std::memcpy(&packet, mapped_region, sizeof(SharedIntentPacket));
        }
        return packet;
    }

    ~IntentOSMemoryBridge() {
        if (mapped_region) munmap(mapped_region, SHM_ARENA_SIZE);
        if (shm_fd != -1) close(shm_fd);
        if (is_host && shm_fd != -1) shm_unlink(SHM_REGION_NAME);
    }
};

int main() {
    std::cout << "=========================================================" << std::endl;
    std::cout << "      INTENTOS C++20 SHARED MEMORY CORE INITIALIZATION   " << std::endl;
    std::cout << "=========================================================\n" << std::endl;

    IntentOSMemoryBridge host_bridge(true);
    if (!host_bridge.initialize()) {
        std::cerr << "[Critical Error] POSIX memory allocation failed." << std::endl;
        return 1;
    }
    std::cout << "[Host Process] Pre-allocated zero-copy RAM segment: " << SHM_REGION_NAME << std::endl;

    // Simulate packing a dynamic muscle intent command frame directly to RAM slots
    SharedIntentPacket out_packet;
    out_packet.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
    out_packet.modality = 1; // EMG
    out_packet.features[0] = 0.742f; // Mock MAV feature calculation
    out_packet.features[1] = 0.891f; // Mock RMS feature calculation
    std::strncpy(out_packet.action_token, "PRIMARY_SELECT", sizeof(out_packet.action_token));
    out_packet.confidence = 0.984f;

    std::cout << "Writing intent frame to Shared Memory block..." << std::endl;
    host_bridge.write_intent(out_packet);

    // Simulate an independent consumer (like a Unity Engine runtime instance) reading that exact same chunk
    IntentOSMemoryBridge client_bridge(false);
    if (client_bridge.initialize()) {
        SharedIntentPacket in_packet = client_bridge.read_intent();
        std::cout << "\n⚡ [ZERO-COPY INTERCEPT SUCCESSFUL]" << std::endl;
        std::cout << "  ├─ Consumer Read Action Token: " << in_packet.action_token << std::endl;
        std::cout << "  ├─ Extracted Stream Power    : MAV=" << in_packet.features[0] << " | RMS=" << in_packet.features[1] << std::endl;
        std::cout << "  └─ Model Confidence Score    : " << in_packet.confidence * 100 << "% Match" << std::endl;
    }

    return 0;
}
