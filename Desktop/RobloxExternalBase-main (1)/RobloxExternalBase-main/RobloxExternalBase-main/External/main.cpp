#include <filesystem>
#include <cstdint>
#include <iostream>
#include <windows.h>
#include <thread>
#include <chrono>
#include <atomic>
#include "src/memory/memory.h"
#include "src/sdk/offsets.h"
#include "src/sdk/sdk.h"
#include "src/core/cache/cache.h"
#include "src/core/globals/globals.h"
#include "src/core/tp_handler/tp_handler.h"
#include "src/core/features/visuals/visuals.h"
#include "src/core/features/aimbot/aimbot.h"
#include "src/core/features/misc/misc.h"
#include "src/core/features/explorer/Explorer.h"
#include "src/render/render.h"

namespace
{
	constexpr const char* app = "RobloxPlayerBeta.exe";
	constexpr const wchar_t* apptitle = L"Roblox";

	bool isgamerunning(const wchar_t* windowTitle)
	{
		HWND hwnd = FindWindowW(NULL, windowTitle);
		return hwnd != NULL;
	}

	void thread()
	{
		while (Globals::running) {
			Globals::camera = Globals::workspace.FindChildByClass("Camera");
			auto localPlayerAddr = memory->read<uintptr_t>(Globals::players.Addr + Offsets::Player::LocalPlayer);
			Globals::localPlayer = RBX::RbxInstance(localPlayerAddr);

			auto character = Globals::localPlayer.GetModelRef();
			if (character.Addr != 0) {
				Misc::RunExploits();
			}

            if (variables::Local::fovChangerEnabled && Globals::camera.Addr != 0) {
                memory->write<float>(Globals::camera.Addr + Offsets::Camera::FieldOfView, variables::Local::fieldOfView);
            }

			static bool lastDesyncState = false;
			if (variables::Local::desyncEnabled != lastDesyncState) {
				auto baseAddr = memory->get_module_address();
				if (baseAddr) {
					auto desyncAddr = baseAddr + Offsets::Desync::PhysicsSenderMaxBandwidthBps;
					if (variables::Local::desyncEnabled) {
						memory->write<float>(desyncAddr, 0.0f);
					} else {
						memory->write<float>(desyncAddr, 5.431432847722991e-41f);
					}
					lastDesyncState = variables::Local::desyncEnabled;
				}
			}

			std::this_thread::sleep_for(std::chrono::milliseconds(1));
		}
	}

	bool init()
	{
		if (!memory->find_process_id(app)) {
			printf("unable to get pid. \n");
			printf("make sure to launch roblox ig. \n");
			system("pause");
			return false;
		}
		if (!memory->attach_to_process(app)) {
			printf("unable to attach roblox.");
			return false;
		}
		if (!memory->find_module_address(app)) {
			printf("unable to find main module adress!");
			return false;
		}
		auto baseAddr = memory->get_module_address();
		if (!baseAddr) {
			printf("base address is null.");
			return false;
		}
		auto fakeDataModelAddr = baseAddr + Offsets::FakeDataModel::Pointer;
		auto fakeDataModel = memory->read<uintptr_t>(fakeDataModelAddr);
		if (!fakeDataModel) {
			printf("fake datamodel pointer is null.");
			return false;
		}
		auto dataModelAddr = fakeDataModel + Offsets::FakeDataModel::RealDataModel;
		auto dataModelPtr = memory->read<uintptr_t>(dataModelAddr);
		if (!dataModelPtr) {
			printf("datamodel pointer is null.");
			return false;
		}
		auto visualEngineAddr = baseAddr + Offsets::VisualEngine::Pointer;
		auto visualEngine = memory->read<uintptr_t>(visualEngineAddr);
		if (!visualEngine) {
			printf("visualengine pointer is null.");
			return false;
		}
		Globals::dataModel = RBX::RbxInstance(dataModelPtr);
		Globals::renderEngine = RBX::RenderEngine(visualEngine);
		Globals::workspace = Globals::dataModel.FindChildByClass("Workspace");
		Globals::players = Globals::dataModel.FindChildByClass("Players");
		Globals::camera = Globals::workspace.FindChildByClass("Camera");
		Globals::gameId = memory->read<uint64_t>(dataModelPtr + Offsets::DataModel::PlaceId);
		Globals::isPhantomForces = (Globals::gameId == Globals::PF_PLACE_ID || 
                                    Globals::gameId == Globals::PF_HUB_ID || 
                                    Globals::gameId == Globals::PF_TEST_ID);
		auto localPlayerAddr = memory->read<uintptr_t>(Globals::players.Addr + Offsets::Player::LocalPlayer);
		Globals::localPlayer = RBX::RbxInstance(localPlayerAddr);
		system("cls");
		std::cout << "[+] Attached successfully\n";
		std::cout << "[+] PlaceId: " << Globals::gameId << "\n";
		if (Globals::isPhantomForces) std::cout << "[+] Game detected: Phantom Forces\n";
		else std::cout << "[+] Game detected: Generic\n";
		return true;
	}
}

std::int32_t main() 
{
	SetConsoleTitleA("Sexy Roblox External");
	if (!init()) return 1;
	OverlayWindow overlay;
	if (!overlay.Initialize()) {
		std::cout << "[!] failed to initialize overlay\n";
		return -1;
	}
	std::cout << "[+] overlay initialized\n";
	std::cout << "[*] press insert to toggle menu\n\n";
	std::thread tpThread(Core::tp_handler::thread);
    std::thread localThread(thread);
    int frameCounter = 0;
    while (memory->IsConnected() && Globals::running) {
        if (!isgamerunning(apptitle)) break;
		if (GetAsyncKeyState(VK_INSERT) & 1) variables::menuOpen = !variables::menuOpen;
		if (Globals::renderEngine.Addr == 0 || Globals::players.Addr == 0 || Globals::localPlayer.Addr == 0) {
			std::this_thread::sleep_for(std::chrono::milliseconds(50));
			continue;
		}
        if (frameCounter % 3 == 0) PlayerCache::updateplayers();
        frameCounter++;
        overlay.BeginFrame();
        overlay.RenderMenu();
        ImDrawList* drawList = ImGui::GetBackgroundDrawList();
        overlay.render(drawList);
        auto viewMatrix = Globals::renderEngine.GetViewMat();
		Aimbot::RunAimbot(viewMatrix);
        Visuals::RenderESP(drawList, viewMatrix);
        if (variables::Explorer::enabled) Explorer::Render();
        overlay.EndFrame();
    }
    Globals::running = false;
    if (tpThread.joinable()) tpThread.join();
    if (localThread.joinable()) localThread.join();
    overlay.Cleanup();
    return 0;
}
