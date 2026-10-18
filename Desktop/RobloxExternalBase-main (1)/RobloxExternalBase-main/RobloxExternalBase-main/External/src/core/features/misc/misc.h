#pragma once

#include "../../variables/variables.h"
#include "../../globals/globals.h"
#include "../../../sdk/sdk.h"
#include "../../../sdk/offsets.h"
#include "../../../memory/memory.h"

#include <cmath>
#include <chrono>

namespace Misc {

    inline void SetCanCollide(RBX::RbxInstance part, bool state) {
        if (!part.Addr) return;
        uintptr_t primitive = memory->read<uintptr_t>(part.Addr + Offsets::BasePart::Primitive);
        if (!primitive) return;

        uint16_t flags = memory->read<uint16_t>(primitive + Offsets::Primitive::Flags);
        if (state) flags |= (uint16_t)Offsets::PrimitiveFlags::CanCollide;
        else flags &= ~(uint16_t)Offsets::PrimitiveFlags::CanCollide;
        
        memory->write<uint16_t>(primitive + Offsets::Primitive::Flags, flags);
    }

    inline RBX::Vec3 GetLookVector(const RBX::Camera::Mat3& rot) {
        return { rot.data[2], rot.data[5], rot.data[8] };
    }

    inline RBX::Vec3 GetRightVector(const RBX::Camera::Mat3& rot) {
        return { rot.data[0], rot.data[3], rot.data[6] };
    }

    inline void RunExploits() {
        RBX::RbxInstance character(0);
        
        if (Globals::isPhantomForces) {
            auto ignore = Globals::workspace.FindChild("Ignore");
            if (ignore.Addr != 0) {
                character = ignore.FindChildByClass("Model");
            }
        } else {
            character = Globals::localPlayer.GetModelRef();
        }
        
        if (character.Addr == 0) return;

        auto humanoid = character.FindChildByClass("Humanoid");
        auto hrp = character.FindChild("HumanoidRootPart");
        
        if (Globals::isPhantomForces && hrp.Addr == 0) {
            auto children = character.GetChildList();
            for (auto& child : children) {
                if (child.FindChildByClass("SpotLight").Addr != 0) {
                    hrp = child;
                    break;
                }
            }
        }

        if (variables::Local::noClipEnabled) {
            auto children = character.GetChildList();
            for (auto& child : children) {
                SetCanCollide(child, false);
            }
        }

        static bool wasJumpPressed = false;
        bool isJumpPressed = (GetAsyncKeyState(VK_SPACE) & 0x8000);
        if (variables::Local::infiniteJumpEnabled && isJumpPressed && !wasJumpPressed) {
            if (hrp.Addr != 0) {
                uintptr_t primitive = memory->read<uintptr_t>(hrp.Addr + Offsets::BasePart::Primitive);
                if (primitive) {
                    RBX::Vec3 vel = memory->read<RBX::Vec3>(primitive + Offsets::Primitive::AssemblyLinearVelocity);
                    vel.Y = 50.0f;
                    memory->write<RBX::Vec3>(primitive + Offsets::Primitive::AssemblyLinearVelocity, vel);
                }
            }
        }
        wasJumpPressed = isJumpPressed;

        RBX::Camera cam(Globals::camera.Addr);

        if (variables::Local::speedEnabled && hrp.Addr != 0) {
            uintptr_t primitive = memory->read<uintptr_t>(hrp.Addr + Offsets::BasePart::Primitive);
            if (primitive) {
                RBX::Camera::Mat3 camRot = cam.GetCameraRotation();
                RBX::Vec3 look = GetLookVector(camRot);
                RBX::Vec3 right = GetRightVector(camRot);
                look.Y = 0; right.Y = 0;

                float moveX = 0, moveZ = 0;
                if (GetAsyncKeyState('W') & 0x8000) { moveX += look.X; moveZ += look.Z; }
                if (GetAsyncKeyState('S') & 0x8000) { moveX -= look.X; moveZ -= look.Z; }
                if (GetAsyncKeyState('A') & 0x8000) { moveX -= right.X; moveZ -= right.Z; }
                if (GetAsyncKeyState('D') & 0x8000) { moveX += right.X; moveZ += right.Z; }

                float mag = sqrtf(moveX * moveX + moveZ * moveZ);
                if (mag > 0.1f) {
                    RBX::Vec3 vel = memory->read<RBX::Vec3>(primitive + Offsets::Primitive::AssemblyLinearVelocity);
                    vel.X = (moveX / mag) * variables::Local::walkSpeed;
                    vel.Z = (moveZ / mag) * variables::Local::walkSpeed;
                    memory->write<RBX::Vec3>(primitive + Offsets::Primitive::AssemblyLinearVelocity, vel);
                }
            }
        }

        if (variables::Local::jumpEnabled && humanoid.Addr != 0) {
            memory->write<float>(humanoid.Addr + Offsets::Humanoid::JumpPower, variables::Local::jumpPower);
            memory->write<uint8_t>(humanoid.Addr + Offsets::Humanoid::UseJumpPower, 1);
        }

        if (variables::Local::flyEnabled && hrp.Addr != 0) {
            uintptr_t primitive = memory->read<uintptr_t>(hrp.Addr + Offsets::BasePart::Primitive);
            if (primitive) {
                RBX::Camera::Mat3 camRot = cam.GetCameraRotation();
                RBX::Vec3 look = GetLookVector(camRot);
                RBX::Vec3 right = GetRightVector(camRot);
                
                RBX::Vec3 flyDir = { 0, 0, 0 };
                if (GetAsyncKeyState('W') & 0x8000) { flyDir.X += look.X; flyDir.Y += look.Y; flyDir.Z += look.Z; }
                if (GetAsyncKeyState('S') & 0x8000) { flyDir.X -= look.X; flyDir.Y -= look.Y; flyDir.Z -= look.Z; }
                if (GetAsyncKeyState('A') & 0x8000) { flyDir.X -= right.X; flyDir.Y -= right.Y; flyDir.Z -= right.Z; }
                if (GetAsyncKeyState('D') & 0x8000) { flyDir.X += right.X; flyDir.Y += right.Y; flyDir.Z += right.Z; }
                if (GetAsyncKeyState(VK_SPACE) & 0x8000) flyDir.Y += 1.0f;
                if (GetAsyncKeyState(VK_SHIFT) & 0x8000) flyDir.Y -= 1.0f;

                float mag = sqrtf(flyDir.X * flyDir.X + flyDir.Y * flyDir.Y + flyDir.Z * flyDir.Z);
                RBX::Vec3 targetVel = { 0, 0, 0 };
                if (mag > 0.1f) {
                    targetVel.X = (flyDir.X / mag) * variables::Local::flySpeed;
                    targetVel.Y = (flyDir.Y / mag) * variables::Local::flySpeed;
                    targetVel.Z = (flyDir.Z / mag) * variables::Local::flySpeed;
                }
                memory->write<RBX::Vec3>(primitive + Offsets::Primitive::AssemblyLinearVelocity, targetVel);
            }
        }

        static float spin_angle = 0.0f;
        static RBX::Camera::Mat3 spin_startRot;
        static bool spin_lastState = false;

        if (variables::Local::spinbotEnabled) {
            if (!spin_lastState) {
                spin_startRot = cam.GetCameraRotation();
                spin_angle = 0.0f;
                spin_lastState = true;
            }

            spin_angle += variables::Local::spinbotSpeed;
            if (spin_angle >= 360.0f) spin_angle -= 360.0f;

            float rad = spin_angle * (3.14159265f / 180.0f);
            float c = cosf(rad);
            float s = sinf(rad);

            RBX::Camera::Mat3 newRot;
            newRot.data[0] = c * spin_startRot.data[0] + s * spin_startRot.data[6];
            newRot.data[1] = c * spin_startRot.data[1] + s * spin_startRot.data[7];
            newRot.data[2] = c * spin_startRot.data[2] + s * spin_startRot.data[8];
            newRot.data[3] = spin_startRot.data[3];
            newRot.data[4] = spin_startRot.data[4];
            newRot.data[5] = spin_startRot.data[5];
            newRot.data[6] = -s * spin_startRot.data[0] + c * spin_startRot.data[6];
            newRot.data[7] = -s * spin_startRot.data[1] + c * spin_startRot.data[7];
            newRot.data[8] = -s * spin_startRot.data[2] + c * spin_startRot.data[8];

            cam.SetCameraRotation(newRot);
        } else {
            spin_lastState = false;
        }
    }
}