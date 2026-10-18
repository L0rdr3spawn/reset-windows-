#pragma once
#include <d3d11.h>
#include "../../../src/sdk/sdk.h"

namespace Globals {

    inline constexpr uint64_t PF_PLACE_ID = 292439477;
    inline constexpr uint64_t PF_HUB_ID = 113491250;
    inline constexpr uint64_t PF_TEST_ID = 986595885;

    inline RBX::RbxInstance dataModel(0);
    inline RBX::RenderEngine renderEngine(0);
    inline RBX::RbxInstance workspace(0);
    inline RBX::RbxInstance players(0);
    inline bool running = true;
    inline RBX::RbxInstance camera(0);
    inline RBX::RbxInstance localPlayer(0);
    inline ID3D11Device* g_pd3dDevice = nullptr;
    inline uint64_t gameId = 0;
    inline bool isPhantomForces = false;
}
