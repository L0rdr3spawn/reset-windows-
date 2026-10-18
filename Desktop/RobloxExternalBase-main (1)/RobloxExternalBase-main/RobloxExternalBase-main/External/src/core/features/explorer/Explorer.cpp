#include "Explorer.h"
#include "../../variables/variables.h"
#include "../../globals/globals.h"
#include "../../../sdk/sdk.h"
#include "../../../../ext/imgui/imgui.h"
#include "ClassImages.h"

#define STB_IMAGE_IMPLEMENTATION
#include "../../../../ext/stb_image.h"

#include <unordered_map>
#include <string>
#include <vector>

void RecursiveDraw(RBX::RbxInstance instance, std::string parentPath);
ID3D11ShaderResourceView* ClassImagesPallete = nullptr;
bool FirstTime = true;

namespace Explorer
{
    void Render()
    {
        if (FirstTime)
        {
            int width, height, channels;
            unsigned char* imageData = stbi_load_from_memory(
                ClassImagesRawData,
                sizeof(ClassImagesRawData),
                &width,
                &height,
                &channels,
                4
            );
            if (imageData && width > 0 && height > 0) {
                D3D11_TEXTURE2D_DESC desc = {};
                desc.Width = width;
                desc.Height = height;
                desc.MipLevels = 1;
                desc.ArraySize = 1;
                desc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
                desc.SampleDesc.Count = 1;
                desc.Usage = D3D11_USAGE_DEFAULT;
                desc.BindFlags = D3D11_BIND_SHADER_RESOURCE;
                desc.CPUAccessFlags = 0;

                D3D11_SUBRESOURCE_DATA initData = {};
                initData.pSysMem = imageData;
                initData.SysMemPitch = width * 4;

                ID3D11Texture2D* texture = nullptr;
                if (Globals::g_pd3dDevice && SUCCEEDED(Globals::g_pd3dDevice->CreateTexture2D(&desc, &initData, &texture))) {
                    Globals::g_pd3dDevice->CreateShaderResourceView(texture, nullptr, &ClassImagesPallete);
                    if (texture) texture->Release();
                }
                stbi_image_free(imageData);
            }
            FirstTime = false;
        }

        if (!Globals::dataModel.Addr) return;

        ImGui::Begin("Instance Explorer", &::variables::Explorer::enabled);
        RecursiveDraw(Globals::dataModel, "NULL");
        ImGui::End();
    }
}

void renderClassIcon(const char* className, ImVec2 size = ImVec2(16, 16)) {
    static std::unordered_map<std::string, int> classIconMap = {
     {"Default", 0}, {"Part", 1}, {"Model", 2}, {"Camera", 5}, {"Script", 6},
     {"ImageLabel", 7}, {"MeshPart", 1}, {"Humanoid", 9}, {"Texture", 10},
     {"Sound", 11}, {"Player", 12}, {"SpotLight", 13}, {"SurfaceLight", 14},
     {"Tool", 17}, {"LocalScript", 18}, {"Workspace", 19}, {"Folder", 77},
    };

    int iconIndex = classIconMap.count(className) ? classIconMap[className] : 0;

    float iconWidth = 16.0f / (float)2352.0f;
    float startU = iconIndex * iconWidth;

    if (ClassImagesPallete)
        ImGui::Image((ImTextureID)ClassImagesPallete, size, ImVec2(startU, 0), ImVec2(startU + iconWidth, 1.0f));
}

bool isLuaValidName(const std::string& str) {
    if (str.empty()) return false;
    if (std::isdigit(str[0])) return false;
    for (char ch : str) {
        if (!std::isalnum(ch) && ch != '_') return false;
    }
    return true;
}

void RecursiveDraw(RBX::RbxInstance instance, std::string parentPath)
{
    if (!instance.Addr) return;

    std::string istanceName = instance.GetName();
    std::string instanceClass = instance.GetClass();
    std::string fullName = istanceName + " [" + instanceClass + "]";

    std::string instancePath;
    if (parentPath == "NULL") {
        instancePath = "game";
    } else if (parentPath == "game") {
        instancePath = "game:GetService(\"" + istanceName + "\")";
    } else {
        instancePath = (!isLuaValidName(istanceName)) ? parentPath + "[\"" + istanceName + "\"]" : parentPath + "." + istanceName;
    }

    auto children = instance.GetChildList();

    if (!children.empty()) {
        std::string unique_id = fullName + "##" + std::to_string(instance.Addr);

        renderClassIcon(instanceClass.c_str());
        ImGui::SameLine();

        bool opened = ImGui::TreeNode(unique_id.c_str());

        if (ImGui::IsItemClicked(1)) {
            ImGui::OpenPopup(("ContextMenu##" + std::to_string(instance.Addr)).c_str());
        }

        if (ImGui::BeginPopup(("ContextMenu##" + std::to_string(instance.Addr)).c_str()))
        {
            if (ImGui::MenuItem("Delete Instance")) {
                memory->write<uintptr_t>(instance.Addr + Offsets::Instance::Parent, 0);
            }
            if (ImGui::MenuItem("Copy Address")) {
                char buf[32];
                sprintf_s(buf, "0x%llX", instance.Addr);
                ImGui::SetClipboardText(buf);
            }
            if (ImGui::MenuItem("Copy Path")) {
                ImGui::SetClipboardText(instancePath.c_str());
            }
            ImGui::EndPopup();
        }

        if (opened) {
            for (const auto& child : children) {
                RecursiveDraw(child, instancePath);
            }
            ImGui::TreePop();
        }
    } else {
        renderClassIcon(instanceClass.c_str());
        ImGui::SameLine();
        ImGui::Selectable(fullName.c_str(), false);

        if (ImGui::IsItemClicked(1)) {
            ImGui::OpenPopup(("ContextMenu##" + std::to_string(instance.Addr)).c_str());
        }

        if (ImGui::BeginPopup(("ContextMenu##" + std::to_string(instance.Addr)).c_str()))
        {
            if (ImGui::MenuItem("Delete Instance")) {
                memory->write<uintptr_t>(instance.Addr + Offsets::Instance::Parent, 0);
            }
            if (ImGui::MenuItem("Copy Address")) {
                char buf[32];
                sprintf_s(buf, "0x%llX", instance.Addr);
                ImGui::SetClipboardText(buf);
            }
            if (ImGui::MenuItem("Copy Path")) {
                ImGui::SetClipboardText(instancePath.c_str());
            }
            ImGui::EndPopup();
        }
    }
}
