#pragma once
#include <vector>
#include <cmath>
#include <algorithm>
#include <windows.h>
#include "../../../memory/memory.h"
#include "../../../sdk/offsets.h"
#include "../../../sdk/sdk.h"
#include "../../globals/globals.h"
#include "../../variables/variables.h"
#include "../../cache/cache.h"
#include "../../../sdk/w2s.h"

namespace Aimbot {

    struct Viewport { short x; short y; };

    inline void SetViewport(RBX::Vec2 target) {
        if (Globals::camera.Addr == 0 || Globals::renderEngine.Addr == 0) return;
        uintptr_t visualEngine = Globals::renderEngine.Addr;
        RBX::Vec2 res = memory->read<RBX::Vec2>(visualEngine + Offsets::VisualEngine::Dimensions);
        Viewport vp = {
            (short)((res.X - target.X) * 2),
            (short)((res.Y - target.Y) * 2)
        };
        memory->write<Viewport>(Globals::camera.Addr + Offsets::Camera::Viewport, vp);
    }

    inline void ResetViewport() {
        if (Globals::camera.Addr == 0 || Globals::renderEngine.Addr == 0) return;
        uintptr_t visualEngine = Globals::renderEngine.Addr;
        RBX::Vec2 res = memory->read<RBX::Vec2>(visualEngine + Offsets::VisualEngine::Dimensions);
        Viewport vp = { (short)res.X, (short)res.Y };
        memory->write<Viewport>(Globals::camera.Addr + Offsets::Camera::Viewport, vp);
    }

    inline void RunAimbot(const RBX::Mat4& viewMatrix) {
        if (!variables::Aimbot::enabled) {
            ResetViewport();
            return;
        }

        bool key = (GetAsyncKeyState(variables::Aimbot::aimbotKey) & 0x8000) || (variables::Aimbot::aimbotKey == 2 && (GetAsyncKeyState(VK_RBUTTON) & 0x8000));
        if (!key && variables::Aimbot::aimType != 2) {
            ResetViewport();
            return;
        }

        float closestDist = variables::Aimbot::fovRadius;
        PlayerCache::CachedPlayer* targetPlayer = nullptr;
        RBX::Vec2 targetScreenPos = { 0, 0 };

        POINT p; GetCursorPos(&p);
        RBX::Vec2 mousePos = { (float)p.x, (float)p.y };

        for (auto& plr : PlayerCache::players) {
            if (!plr.isValid) continue;
            if (variables::Aimbot::teamCheck && plr.teamAddr != 0 && plr.teamAddr == PlayerCache::localTeamAddr) continue;

            RBX::Vec3 targetPos;
            if (variables::Aimbot::aimTarget == 0) targetPos = RBX::RbxInstance(plr.headAddr).GetPos();
            else targetPos = RBX::RbxInstance(plr.rootPartAddr).GetPos();

            if (variables::Aimbot::prediction) {
                uintptr_t prim = memory->read<uintptr_t>(plr.rootPartAddr + Offsets::BasePart::Primitive);
                if (prim != 0) {
                    RBX::Vec3 vel = memory->read<RBX::Vec3>(prim + Offsets::Primitive::AssemblyLinearVelocity);
                    targetPos.X += vel.X * 0.15f;
                    targetPos.Y += vel.Y * 0.15f;
                    targetPos.Z += vel.Z * 0.15f;
                }
            }

            RBX::Vec2 screenPos = W2S::WorldToScreen(targetPos, viewMatrix);
            if (screenPos.X == 0) continue;

            float dist = sqrtf(powf(screenPos.X - mousePos.X, 2) + powf(screenPos.Y - mousePos.Y, 2));

            if (dist < closestDist) {
                closestDist = dist;
                targetPlayer = &plr;
                targetScreenPos = screenPos;
            }
        }

        if (targetPlayer) {
            if (variables::Aimbot::aimType == 0) {
                float dx = targetScreenPos.X - mousePos.X;
                float dy = targetScreenPos.Y - mousePos.Y;
                if (variables::Aimbot::smoothning) {
                    dx /= variables::Aimbot::smoothing;
                    dy /= variables::Aimbot::smoothing;
                }
                mouse_event(MOUSEEVENTF_MOVE, (DWORD)dx, (DWORD)dy, 0, 0);
                ResetViewport();
            } else if (variables::Aimbot::aimType == 1) {
                RBX::Vec3 targetPos;
                if (variables::Aimbot::aimTarget == 0) targetPos = RBX::RbxInstance(targetPlayer->headAddr).GetPos();
                else targetPos = RBX::RbxInstance(targetPlayer->rootPartAddr).GetPos();
                RBX::Camera cam(Globals::camera.Addr);
                RBX::Vec3 camPos = cam.GetCameraPosition();
                RBX::Vec3 dir = { targetPos.X - camPos.X, targetPos.Y - camPos.Y, targetPos.Z - camPos.Z };
                float dist = sqrtf(dir.X * dir.X + dir.Y * dir.Y + dir.Z * dir.Z);
                RBX::Vec3 look = { dir.X / dist, dir.Y / dist, dir.Z / dist };
                float yaw = atan2f(-look.X, -look.Z);
                float pitch = asinf(look.Y);
                if (variables::Aimbot::smoothning) {
                    RBX::Camera::Mat3 curRot = cam.GetCameraRotation();
                    float curYaw = atan2f(-curRot.data[2], -curRot.data[8]);
                    float curPitch = asinf(curRot.data[5]);
                    float diffYaw = yaw - curYaw;
                    if (diffYaw > 3.14159f) diffYaw -= 6.28318f;
                    if (diffYaw < -3.14159f) diffYaw += 6.28318f;
                    yaw = curYaw + diffYaw / variables::Aimbot::smoothing;
                    pitch = curPitch + (pitch - curPitch) / variables::Aimbot::smoothing;
                }
                float cp = cosf(pitch), sp = sinf(pitch);
                float cy = cosf(yaw), sy = sinf(yaw);
                RBX::Camera::Mat3 newRot;
                newRot.data[0] = cy; newRot.data[1] = 0; newRot.data[2] = sy;
                newRot.data[3] = sy * sp; newRot.data[4] = cp; newRot.data[5] = -cy * sp;
                newRot.data[6] = -sy * cp; newRot.data[7] = sp; newRot.data[8] = cy * cp;
                cam.SetCameraRotation(newRot);
                ResetViewport();
            } else if (variables::Aimbot::aimType == 2) {
                SetViewport(targetScreenPos);
            }
        } else {
            ResetViewport();
        }
    }
}
