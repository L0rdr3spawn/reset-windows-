#pragma once
#include "../../../../ext/imgui/imgui.h"
#include "../../../../src/core/cache/cache.h"
#include "../../../../src/core/variables/variables.h"
#include "../../../../src/sdk/w2s.h"
#include <algorithm>
#include <cmath>
#include <string>

namespace Visuals {

inline void DrawOutlinedText(ImDrawList *drawList, const ImVec2 &pos, const std::string &text, ImU32 textColor) {
  drawList->AddText(ImVec2(pos.x - 1, pos.y), IM_COL32(0, 0, 0, 255), text.c_str());
  drawList->AddText(ImVec2(pos.x + 1, pos.y), IM_COL32(0, 0, 0, 255), text.c_str());
  drawList->AddText(ImVec2(pos.x, pos.y - 1), IM_COL32(0, 0, 0, 255), text.c_str());
  drawList->AddText(ImVec2(pos.x, pos.y + 1), IM_COL32(0, 0, 0, 255), text.c_str());
  drawList->AddText(pos, textColor, text.c_str());
}

inline void RenderESP(ImDrawList *drawList, const RBX::Mat4 &viewMatrix) {
  if (!variables::ESP::enabled) return;

  for (auto &plr : PlayerCache::players) {
    if (!plr.isValid) continue;
    if (variables::ESP::teamCheck && plr.teamAddr != 0 && plr.teamAddr == PlayerCache::localTeamAddr) continue;

    RBX::Vec3 headPos, hrpPos;
    if (plr.headAddr != 0) headPos = RBX::RbxInstance(plr.headAddr).GetPos();
    if (plr.rootPartAddr != 0) hrpPos = RBX::RbxInstance(plr.rootPartAddr).GetPos();

    RBX::Vec2 screenHead = W2S::WorldToScreen({headPos.X, headPos.Y + 1.5f, headPos.Z}, viewMatrix);
    RBX::Vec2 screenFoot = W2S::WorldToScreen({hrpPos.X, hrpPos.Y - 3.0f, hrpPos.Z}, viewMatrix);

    if (screenHead.X == 0 || screenFoot.X == 0) continue;

    float height = screenFoot.Y - screenHead.Y;
    float width = height / 2.0f;
    float x = screenHead.X - width / 2.0f;
    float y = screenHead.Y;

    if (variables::ESP::boxes) {
        drawList->AddRect(ImVec2(x - 1, y - 1), ImVec2(x + width + 1, y + height + 1), IM_COL32(0, 0, 0, 255));
        drawList->AddRect(ImVec2(x + 1, y + 1), ImVec2(x + width - 1, y + height - 1), IM_COL32(0, 0, 0, 255));
        drawList->AddRect(ImVec2(x, y), ImVec2(x + width, y + height), IM_COL32(255, 255, 255, 255));
    }

    if (variables::ESP::healthBar) {
        float healthPct = std::clamp(plr.health / plr.maxHealth, 0.0f, 1.0f);
        drawList->AddRectFilled(ImVec2(x - 6, y - 1), ImVec2(x - 2, y + height + 1), IM_COL32(0, 0, 0, 255));
        drawList->AddRectFilled(ImVec2(x - 5, y + height - (height * healthPct)), ImVec2(x - 3, y + height), IM_COL32(0, 255, 0, 255));
    }

    if (variables::ESP::healthText) {
        std::string hText = std::to_string((int)plr.health) + "HP";
        DrawOutlinedText(drawList, ImVec2(x - 5, y + height - (height * (plr.health/plr.maxHealth)) - 10), hText, IM_COL32(255, 255, 255, 255));
    }

    if (variables::ESP::names) {
        ImVec2 tSize = ImGui::CalcTextSize(plr.name.c_str());
        DrawOutlinedText(drawList, ImVec2(x + width/2.0f - tSize.x/2.0f, y - tSize.y - 2), plr.name, IM_COL32(255, 255, 255, 255));
    }

    if (variables::ESP::distance) {
        std::string dText = std::to_string((int)plr.distance) + "m";
        ImVec2 tSize = ImGui::CalcTextSize(dText.c_str());
        DrawOutlinedText(drawList, ImVec2(x + width/2.0f - tSize.x/2.0f, y + height + 2), dText, IM_COL32(255, 255, 255, 255));
    }

    if (variables::ESP::snaplines) {
        drawList->AddLine(ImVec2(ImGui::GetIO().DisplaySize.x/2, ImGui::GetIO().DisplaySize.y), ImVec2(x + width/2, y + height), IM_COL32(255, 255, 255, 255));
    }
  }
}
}
