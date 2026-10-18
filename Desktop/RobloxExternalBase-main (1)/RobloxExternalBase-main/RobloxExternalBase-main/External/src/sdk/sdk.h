#pragma once
#include "../../src/sdk/offsets.h"
#include "../../src/memory/memory.h"
#include <string>
#include <vector>
#include <cmath>

namespace RBX {

    struct Vec2 {
        float X{ 0 };
        float Y{ 0 };
    };

    struct Vec3 {
        float X{ 0 };
        float Y{ 0 };
        float Z{ 0 };
    };

    struct Vec4 {
        float X{ 0 };
        float Y{ 0 };
        float Z{ 0 };
        float W{ 0 };
    };

    struct Mat4 {
        float data[16];
    };

    struct CFrame {
        float data[12];

        Vec3 GetRightVector() const {
            return { data[0], data[3], data[6] };
        }

        Vec3 GetUpVector() const {
            return { data[1], data[4], data[7] };
        }

        Vec3 GetLookVector() const {
            return { data[2], data[5], data[8] };
        }

        Vec3 GetPosition() const {
            return { data[9], data[10], data[11] };
        }
    };

    struct Viewport {
        short x;
        short y;
    };

    class RbxInstance {
    public:
        uintptr_t Addr;

        RbxInstance(uintptr_t addr) : Addr(addr) {}

        std::string GetName() {
            uintptr_t namePtr = memory->read<uintptr_t>(Addr + Offsets::Instance::Name);
            if (namePtr == 0) return "";
            return memory->read_string(namePtr);
        }

        std::string GetClass() {
            uintptr_t classDesc = memory->read<uintptr_t>(Addr + Offsets::Instance::ClassDescriptor);
            if (classDesc == 0) return "";
            uintptr_t namePtr = memory->read<uintptr_t>(classDesc + Offsets::Instance::ClassName);
            if (namePtr == 0) return "";
            return memory->read_string(namePtr);
        }

        RbxInstance GetParent() {
            return RbxInstance(memory->read<uintptr_t>(Addr + Offsets::Instance::Parent));
        }

        std::vector<RbxInstance> GetChildList() {
            std::vector<RbxInstance> childList;
            if (Addr == 0) return childList;
            uintptr_t childStart = memory->read<uintptr_t>(Addr + Offsets::Instance::ChildrenStart);
            if (childStart == 0) return childList;
            uintptr_t childEnd = memory->read<uintptr_t>(childStart + Offsets::Instance::ChildrenEnd);
            uintptr_t current = memory->read<uintptr_t>(childStart);
            if (childEnd == 0 || current == 0 || childEnd < current) return childList;
            size_t childCount = 0;
            for (uintptr_t ptr = current; ptr < childEnd && childCount < 4096; ptr += 0x10, ++childCount) {
                uintptr_t childAddr = memory->read<uintptr_t>(ptr);
                if (childAddr == 0) continue;
                childList.emplace_back(childAddr);
            }
            return childList;
        }

        RbxInstance FindChild(const std::string& targetName) {
            auto children = GetChildList();
            for (auto& child : children) {
                if (child.GetName() == targetName) {
                    return child;
                }
            }
            return RbxInstance(0);
        }

        RbxInstance FindChildByClass(const std::string& targetClass) {
            auto children = GetChildList();
            for (auto& child : children) {
                if (child.GetClass() == targetClass) {
                    return child;
                }
            }
            return RbxInstance(0);
        }

        RbxInstance WaitChild(const std::string& targetName) {
            while (true) {
                auto children = GetChildList();
                for (auto& child : children) {
                    if (child.GetName() == targetName) {
                        return child;
                    }
                }
            }
        }

        uintptr_t GetPrimitivePtr() {
            return memory->read<uintptr_t>(Addr + Offsets::BasePart::Primitive);
        }

        Vec3 GetPos() {
            uintptr_t prim = GetPrimitivePtr();
            if (prim == 0) return {};
            return memory->read<Vec3>(prim + Offsets::Primitive::Position);
        }

        CFrame GetCFrame() {
            uintptr_t prim = GetPrimitivePtr();
            if (prim == 0) return {};
            return memory->read<CFrame>(prim + Offsets::Primitive::Rotation);
        }

        RbxInstance GetModelRef() {
            return RbxInstance(memory->read<uintptr_t>(Addr + Offsets::Player::ModelInstance));
        }

        float CalcDistance(const Vec3& targetPos) {
            Vec3 currentPos = GetPos();
            float dx = currentPos.X - targetPos.X;
            float dy = currentPos.Y - targetPos.Y;
            float dz = currentPos.Z - targetPos.Z;
            return sqrtf(dx * dx + dy * dy + dz * dz);
        }
    };

    class Camera : public RbxInstance {
    public:
        Camera(uintptr_t addr) : RbxInstance(addr) {}
        struct Mat3 {
            float data[9];
        };
        Mat3 GetCameraRotation() {
            if (!Addr) return Mat3{};
            return memory->read<Mat3>(Addr + Offsets::Camera::Rotation);
        }
        Vec3 GetCameraPosition() {
            if (!Addr) return Vec3{};
            return memory->read<Vec3>(Addr + Offsets::Camera::Position);
        }
        void SetCameraRotation(Mat3 Value) {
            if (!Addr) return;
            memory->write<Mat3>(Addr + Offsets::Camera::Rotation, Value);
        }
        void ResetViewport() {
            if (!Addr) return;
            Vec2 screenDims{ static_cast<float>(GetSystemMetrics(SM_CXSCREEN)), static_cast<float>(GetSystemMetrics(SM_CYSCREEN)) };
            Viewport vp;
            vp.x = static_cast<short>(screenDims.X);
            vp.y = static_cast<short>(screenDims.Y);
            memory->write<Viewport>(Addr + Offsets::Camera::Viewport, vp);
        }
        void SetViewportTarget(Vec2 target) {
            if (!Addr) return;
            Vec2 screenDims{ static_cast<float>(GetSystemMetrics(SM_CXSCREEN)), static_cast<float>(GetSystemMetrics(SM_CYSCREEN)) };
            Viewport vp;
            vp.x = static_cast<short>((screenDims.X - target.X) * 2);
            vp.y = static_cast<short>((screenDims.Y - target.Y) * 2);
            memory->write<Viewport>(Addr + Offsets::Camera::Viewport, vp);
        }
    };

    class RenderEngine : public RbxInstance {
    public:
        RenderEngine(uintptr_t addr) : RbxInstance(addr) {}
        Mat4 GetViewMat() {
            return memory->read<Mat4>(Addr + Offsets::VisualEngine::ViewMatrix);
        }
    };

}
