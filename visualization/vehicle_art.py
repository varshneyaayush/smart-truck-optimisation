"""
visualization/vehicle_art.py
Enterprise vector SVG illustrations for the fleet catalogue:
- T1: 14 ft Medium Box Truck (Visibly compact, 2-axle urban delivery)
- T2: 17 ft Heavy Carrier (Visibly medium-large, tandem axle with aero deflector)
- T3: 20 ft Freight Truck (Visibly largest, long-haul high-cube with dual rear bogies)

All SVGs are rendered on a standardized 360x140 canvas with a shared floor baseline,
making the physical length and volume differences immediately obvious and proportional.
"""

def get_vehicle_svg(vehicle_id: str, width: str = "100%", height: int = 140) -> str:
    """
    Returns an inline SVG string for the specified vehicle ID.
    All illustrations share the same baseline (y=122) and ground shadow (y=128),
    allowing immediate visual comparison of vehicle sizes.
    """
    if vehicle_id == "T1":
        # T1: 14 ft Urban Delivery Truck - Visibly COMPACT (Total length ~230px, Box: 140x70)
        return f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 140" width="{width}" height="{height}" style="display:block; margin:0 auto; max-width:360px;">
            <defs>
                <linearGradient id="t1CabGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#9E0127"/>
                    <stop offset="100%" stop-color="#7F011F"/>
                </linearGradient>
                <linearGradient id="t1BoxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#FFFFFF"/>
                    <stop offset="100%" stop-color="#F5EBD0"/>
                </linearGradient>
                <linearGradient id="t1WinGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#E1F0F8"/>
                    <stop offset="100%" stop-color="#96C2D6"/>
                </linearGradient>
            </defs>
            <!-- Ground Shadow (Compact) -->
            <ellipse cx="180" cy="128" rx="120" ry="5" fill="#E2D8C3" opacity="0.8"/>
            <!-- Steel Chassis -->
            <rect x="75" y="104" width="205" height="8" rx="2" fill="#2E2E2E"/>
            <rect x="145" y="107" width="28" height="7" rx="1" fill="#4A4A4A"/>
            <!-- Cargo Box: Compact 14ft (L=140, H=70) -->
            <rect x="75" y="34" width="140" height="70" rx="3" fill="url(#t1BoxGrad)" stroke="#C8B898" stroke-width="1.8"/>
            <!-- Horizontal Rib Lines -->
            <line x1="75" y1="52" x2="215" y2="52" stroke="#EAD9BD" stroke-width="1" stroke-dasharray="3,3"/>
            <line x1="75" y1="70" x2="215" y2="70" stroke="#EAD9BD" stroke-width="1" stroke-dasharray="3,3"/>
            <line x1="75" y1="88" x2="215" y2="88" stroke="#EAD9BD" stroke-width="1" stroke-dasharray="3,3"/>
            <!-- Rear Door Frame Indicator -->
            <rect x="75" y="36" width="9" height="66" fill="#E8DBC0" opacity="0.7"/>
            <line x1="84" y1="36" x2="84" y2="104" stroke="#7F011F" stroke-width="1.5"/>
            <!-- Corner Protectors -->
            <rect x="75" y="34" width="5" height="5" fill="#7F011F"/>
            <rect x="210" y="34" width="5" height="5" fill="#7F011F"/>
            <rect x="75" y="99" width="5" height="5" fill="#7F011F"/>
            <rect x="210" y="99" width="5" height="5" fill="#7F011F"/>
            <!-- Livery Accent Stripe -->
            <rect x="88" y="66" width="120" height="6" rx="2" fill="#7F011F"/>
            <text x="94" y="71" font-family="'Inter', sans-serif" font-size="5" font-weight="700" fill="#FFFFFF" letter-spacing="1">14 FT URBAN FLEET</text>
            <!-- Cab Roof Wind Fairing (Small) -->
            <path d="M215,50 L242,56 L215,64 Z" fill="#7F011F"/>
            <!-- Compact Cab -->
            <path d="M215,56 L248,56 Q262,58 268,72 L278,92 Q281,99 279,106 L215,106 Z" fill="url(#t1CabGrad)" stroke="#5A0016" stroke-width="1.2"/>
            <!-- Windows -->
            <path d="M246,62 L260,62 Q267,69 271,78 L246,78 Z" fill="url(#t1WinGrad)" stroke="#222222" stroke-width="0.8"/>
            <path d="M224,62 L242,62 L242,78 L224,78 Z" fill="url(#t1WinGrad)" stroke="#222222" stroke-width="0.8"/>
            <!-- Headlight & Front Bumper -->
            <rect x="276" y="92" width="5" height="5" rx="1.5" fill="#FFE082" stroke="#D4A017" stroke-width="0.6"/>
            <path d="M275,98 L283,98 Q285,103 281,108 L271,108 Z" fill="#3A3A3A"/>
            <!-- Single Rear Wheel -->
            <g transform="translate(115, 114)">
                <circle cx="0" cy="0" r="14" fill="#222222"/>
                <circle cx="0" cy="0" r="8" fill="#666666"/>
                <circle cx="0" cy="0" r="4" fill="#E0E0E0"/>
                <circle cx="0" cy="0" r="1.5" fill="#222222"/>
            </g>
            <!-- Front Wheel -->
            <g transform="translate(252, 114)">
                <circle cx="0" cy="0" r="14" fill="#222222"/>
                <circle cx="0" cy="0" r="8" fill="#666666"/>
                <circle cx="0" cy="0" r="4" fill="#E0E0E0"/>
                <circle cx="0" cy="0" r="1.5" fill="#222222"/>
            </g>
            <!-- Visual Scale Tag -->
            <g transform="translate(86, 40)">
                <rect x="0" y="0" width="34" height="12" rx="3" fill="#7F011F"/>
                <text x="17" y="9" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">T1 • 14 FT</text>
            </g>
        </svg>
        """
    elif vehicle_id == "T2":
        # T2: 17 ft Heavy Carrier - Visibly MEDIUM (Total length ~285px, Box: 185x80)
        return f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 140" width="{width}" height="{height}" style="display:block; margin:0 auto; max-width:360px;">
            <defs>
                <linearGradient id="t2CabGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#9E0127"/>
                    <stop offset="100%" stop-color="#6A0018"/>
                </linearGradient>
                <linearGradient id="t2BoxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#FFFFFF"/>
                    <stop offset="100%" stop-color="#F2E6C8"/>
                </linearGradient>
                <linearGradient id="t2WinGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#E1F0F8"/>
                    <stop offset="100%" stop-color="#8DBDD4"/>
                </linearGradient>
            </defs>
            <!-- Ground Shadow (Medium) -->
            <ellipse cx="180" cy="128" rx="145" ry="5.5" fill="#E2D8C3" opacity="0.8"/>
            <!-- Steel Chassis -->
            <rect x="42" y="104" width="260" height="9" rx="2" fill="#282828"/>
            <rect x="155" y="107" width="38" height="8" rx="1.5" fill="#444444"/>
            <!-- Cargo Box: Medium 17ft (L=185, H=80) -->
            <rect x="42" y="24" width="185" height="80" rx="3.5" fill="url(#t2BoxGrad)" stroke="#C8B898" stroke-width="2"/>
            <!-- Rib Lines -->
            <line x1="42" y1="44" x2="227" y2="44" stroke="#EAD9BD" stroke-width="1" stroke-dasharray="4,4"/>
            <line x1="42" y1="64" x2="227" y2="64" stroke="#EAD9BD" stroke-width="1" stroke-dasharray="4,4"/>
            <line x1="42" y1="84" x2="227" y2="84" stroke="#EAD9BD" stroke-width="1" stroke-dasharray="4,4"/>
            <!-- Rear Frame -->
            <rect x="42" y="26" width="10" height="76" fill="#E8DBC0" opacity="0.7"/>
            <line x1="52" y1="26" x2="52" y2="104" stroke="#7F011F" stroke-width="1.8"/>
            <!-- Corner Protectors -->
            <rect x="42" y="24" width="6" height="6" fill="#7F011F"/>
            <rect x="221" y="24" width="6" height="6" fill="#7F011F"/>
            <rect x="42" y="98" width="6" height="6" fill="#7F011F"/>
            <rect x="221" y="98" width="6" height="6" fill="#7F011F"/>
            <!-- Livery Accent Stripe -->
            <rect x="56" y="60" width="160" height="7" rx="2" fill="#7F011F"/>
            <text x="64" y="65.5" font-family="'Inter', sans-serif" font-size="5.5" font-weight="700" fill="#FFFFFF" letter-spacing="1.2">17 FT HEAVY CARRIER</text>
            <!-- Aerodynamic Roof Fairing -->
            <path d="M227,26 Q250,30 262,48 L227,48 Z" fill="#7F011F"/>
            <!-- Medium-Duty Sleeper Cab -->
            <path d="M227,48 L262,48 Q274,52 282,68 L294,92 Q298,100 295,108 L227,108 Z" fill="url(#t2CabGrad)" stroke="#500012" stroke-width="1.3"/>
            <!-- Windows -->
            <path d="M258,54 L274,54 Q282,63 286,74 L258,74 Z" fill="url(#t2WinGrad)" stroke="#1F1F1F" stroke-width="0.8"/>
            <path d="M234,54 L254,54 L254,74 L234,74 Z" fill="url(#t2WinGrad)" stroke="#1F1F1F" stroke-width="0.8"/>
            <!-- Heavy Bumper & LED Lights -->
            <rect x="294" y="92" width="6" height="6" rx="1.5" fill="#FFE082" stroke="#D4A017" stroke-width="0.7"/>
            <path d="M292,98 L302,98 Q304,105 300,111 L288,111 Z" fill="#333333"/>
            <!-- Dual Rear Tandem Wheels -->
            <g transform="translate(80, 114)">
                <circle cx="0" cy="0" r="15" fill="#202020"/>
                <circle cx="0" cy="0" r="9" fill="#5F5F5F"/>
                <circle cx="0" cy="0" r="4.5" fill="#DBDBDB"/>
                <circle cx="0" cy="0" r="1.5" fill="#202020"/>
            </g>
            <g transform="translate(114, 114)">
                <circle cx="0" cy="0" r="15" fill="#202020"/>
                <circle cx="0" cy="0" r="9" fill="#5F5F5F"/>
                <circle cx="0" cy="0" r="4.5" fill="#DBDBDB"/>
                <circle cx="0" cy="0" r="1.5" fill="#202020"/>
            </g>
            <!-- Front Steer Wheel -->
            <g transform="translate(268, 114)">
                <circle cx="0" cy="0" r="15" fill="#202020"/>
                <circle cx="0" cy="0" r="9" fill="#5F5F5F"/>
                <circle cx="0" cy="0" r="4.5" fill="#DBDBDB"/>
                <circle cx="0" cy="0" r="1.5" fill="#202020"/>
            </g>
            <!-- Badge overlay -->
            <g transform="translate(56, 32)">
                <rect x="0" y="0" width="38" height="13" rx="3" fill="#7F011F"/>
                <text x="19" y="9.5" font-family="'Inter', sans-serif" font-size="8" font-weight="700" fill="#FFFFFF" text-anchor="middle">T2 • 17 FT</text>
            </g>
        </svg>
        """
    else:
        # T3: 20 ft High-Capacity Freight Truck - Visibly LARGEST (Total length ~335px, Box: 235x92)
        return f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 140" width="{width}" height="{height}" style="display:block; margin:0 auto; max-width:360px;">
            <defs>
                <linearGradient id="t3CabGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#8E0124"/>
                    <stop offset="100%" stop-color="#4A0012"/>
                </linearGradient>
                <linearGradient id="t3BoxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#FFFFFF"/>
                    <stop offset="100%" stop-color="#EFE2C2"/>
                </linearGradient>
                <linearGradient id="t3WinGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#E1F0F8"/>
                    <stop offset="100%" stop-color="#82B3CB"/>
                </linearGradient>
            </defs>
            <!-- Ground Shadow (Full Length) -->
            <ellipse cx="180" cy="128" rx="168" ry="6" fill="#E2D8C3" opacity="0.85"/>
            <!-- Heavy Linehaul Chassis -->
            <rect x="15" y="104" width="320" height="10" rx="2.5" fill="#202020"/>
            <rect x="160" y="107" width="55" height="9" rx="2" fill="#3E3E3E"/>
            <rect x="220" y="108" width="25" height="7" rx="1.5" fill="#3E3E3E"/>
            <!-- High-Cube Cargo Box: 20ft (L=235, H=92) -->
            <rect x="15" y="12" width="235" height="92" rx="4" fill="url(#t3BoxGrad)" stroke="#BFAD8A" stroke-width="2.2"/>
            <!-- Reinforcement Ribs -->
            <line x1="15" y1="35" x2="250" y2="35" stroke="#E5D6B6" stroke-width="1.2" stroke-dasharray="5,5"/>
            <line x1="15" y1="58" x2="250" y2="58" stroke="#E5D6B6" stroke-width="1.2" stroke-dasharray="5,5"/>
            <line x1="15" y1="81" x2="250" y2="81" stroke="#E5D6B6" stroke-width="1.2" stroke-dasharray="5,5"/>
            <!-- High-Cube Rear Security Frame -->
            <rect x="15" y="14" width="13" height="88" fill="#E8DBC0" opacity="0.7"/>
            <line x1="28" y1="14" x2="28" y2="104" stroke="#7F011F" stroke-width="2.2"/>
            <rect x="20" y="48" width="5" height="15" rx="1" fill="#7F011F"/> <!-- Lock rod -->
            <!-- Corner Brackets -->
            <rect x="15" y="12" width="7" height="7" fill="#7F011F"/>
            <rect x="243" y="12" width="7" height="7" fill="#7F011F"/>
            <rect x="15" y="97" width="7" height="7" fill="#7F011F"/>
            <rect x="243" y="97" width="7" height="7" fill="#7F011F"/>
            <!-- Livery Banner -->
            <rect x="34" y="54" width="205" height="8" rx="2" fill="#7F011F"/>
            <text x="42" y="60" font-family="'Inter', sans-serif" font-size="6" font-weight="700" fill="#FFFFFF" letter-spacing="1.5">20 FT FREIGHT MASTER HIGH-CUBE</text>
            <!-- Heavy Aerodynamic High-Roof Fairing -->
            <path d="M250,12 Q276,16 290,38 L250,38 Z" fill="#7F011F"/>
            <!-- Heavy Long-Haul Cab -->
            <path d="M250,38 L290,38 Q302,42 312,62 L326,90 Q330,98 328,108 L250,108 Z" fill="url(#t3CabGrad)" stroke="#400010" stroke-width="1.5"/>
            <!-- Windows -->
            <path d="M284,44 L304,44 Q312,54 316,68 L284,68 Z" fill="url(#t3WinGrad)" stroke="#1A1A1A" stroke-width="1"/>
            <path d="M258,44 L280,44 L280,68 L258,68 Z" fill="url(#t3WinGrad)" stroke="#1A1A1A" stroke-width="1"/>
            <!-- Dual Fog & Headlights -->
            <rect x="325" y="88" width="7" height="7" rx="1.5" fill="#FFF9C4" stroke="#D4A017" stroke-width="0.8"/>
            <rect x="325" y="97" width="6" height="4" rx="1" fill="#FFE082"/>
            <path d="M322,96 L334,96 Q336,104 330,111 L316,111 Z" fill="#2B2B2B"/>
            <!-- Dual Rear Tandem Wheels (Heavy Bogie) -->
            <g transform="translate(56, 114)">
                <circle cx="0" cy="0" r="16" fill="#1C1C1C"/>
                <circle cx="0" cy="0" r="9.5" fill="#555555"/>
                <circle cx="0" cy="0" r="5" fill="#CCCCCC"/>
                <circle cx="0" cy="0" r="1.5" fill="#1C1C1C"/>
            </g>
            <g transform="translate(94, 114)">
                <circle cx="0" cy="0" r="16" fill="#1C1C1C"/>
                <circle cx="0" cy="0" r="9.5" fill="#555555"/>
                <circle cx="0" cy="0" r="5" fill="#CCCCCC"/>
                <circle cx="0" cy="0" r="1.5" fill="#1C1C1C"/>
            </g>
            <!-- Heavy Steer Axle -->
            <g transform="translate(295, 114)">
                <circle cx="0" cy="0" r="16" fill="#1C1C1C"/>
                <circle cx="0" cy="0" r="9.5" fill="#555555"/>
                <circle cx="0" cy="0" r="5" fill="#CCCCCC"/>
                <circle cx="0" cy="0" r="1.5" fill="#1C1C1C"/>
            </g>
            <!-- Scale Badge -->
            <g transform="translate(34, 22)">
                <rect x="0" y="0" width="42" height="14" rx="3" fill="#7F011F"/>
                <text x="21" y="10.5" font-family="'Inter', sans-serif" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">T3 • 20 FT</text>
            </g>
        </svg>
        """
