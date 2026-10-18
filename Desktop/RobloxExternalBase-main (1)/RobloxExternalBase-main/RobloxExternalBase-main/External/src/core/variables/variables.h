#pragma once
#include <string>

namespace variables {
    inline bool menuOpen = false;
    inline int selectedTab = 0;

    namespace Aimbot {
        inline bool enabled = false;
        inline bool teamCheck = true;
        inline bool showFOV = false;
        inline float fovRadius = 100.0f;
        inline float smoothing = 5.0f;
        inline bool smoothning = false;
        inline int aimTarget = 0;
        inline int aimType = 0;
        inline int aimbotKey = 2;
        inline bool prediction = false;
        inline float predictionX = 0.0f;
        inline float predictionY = 0.0f;
    }

    namespace ESP {
        inline bool enabled = false;
        inline bool teamCheck = true;
        inline bool boxes = false;
        inline bool names = true;
        inline bool distance = true;
        inline bool healthBar = true;
        inline bool healthText = false;
        inline bool skeleton = false;
        inline bool weapon = false;
        inline bool snaplines = false;
        inline int snaplinesOrigin = 3;
        inline int snaplinesDestination = 0;
        inline int snaplinesStyle = 0;
        inline float snaplinesThickness = 1.0f;
        inline bool snaplinesOutline = true;
    }

    namespace Local {
        inline bool infiniteJumpEnabled = false;
        inline bool noClipEnabled = false;
        inline bool speedEnabled = false;
        inline float walkSpeed = 16.0f;
        inline bool jumpEnabled = false;
        inline float jumpPower = 50.0f;
        inline bool desyncEnabled = false;
        inline bool flyEnabled = false;
        inline float flySpeed = 50.0f;
        inline bool spinbotEnabled = false;
        inline float spinbotSpeed = 10.0f;
        inline bool fovChangerEnabled = false;
        inline float fieldOfView = 70.0f;
    }

    namespace Settings {
        inline bool customPathEnabled = false;
        inline char customPath[256] = "";
    }

    namespace Explorer {
        inline bool enabled = false;
    }
}
