"""RTCM 3.x message type definitions.

Comprehensive lookup table mapping RTCM 3.x message type numbers
to human-readable descriptions. Covers legacy observations, MSM,
SSR, ephemerides, station info, and common proprietary messages.
"""

RTCM_MESSAGE_TYPES = {
    # GPS Legacy Observations
    1001: "GPS L1 Code & Phase",
    1002: "GPS L1 Code & Phase (Extended)",
    1003: "GPS L1/L2 Code & Phase",
    1004: "GPS L1/L2 Code & Phase (Extended)",

    # Station Information
    1005: "Stationary RTK Reference Station ARP",
    1006: "Stationary RTK Reference Station ARP with Height",
    1007: "Antenna Descriptor",
    1008: "Antenna Descriptor & Serial Number",

    # GLONASS Legacy Observations
    1009: "GLONASS L1 Code & Phase",
    1010: "GLONASS L1 Code & Phase (Extended)",
    1011: "GLONASS L1/L2 Code & Phase",
    1012: "GLONASS L1/L2 Code & Phase (Extended)",

    # System & Network
    1013: "System Parameters",
    1014: "Network Auxiliary Station Data",
    1015: "GPS Ionospheric Correction Differences",
    1016: "GPS Geometric Correction Differences",
    1017: "GPS Combined Geometric & Ionospheric Corrections",

    # Ephemerides
    1019: "GPS Satellite Ephemerides",
    1020: "GLONASS Satellite Ephemerides",

    # Transformation Parameters
    1021: "Helmert/Abridged Molodenski Transformation",
    1022: "Molodenski-Badekas Transformation",
    1023: "Residuals, Ellipsoidal Grid Representation",
    1024: "Residuals, Plane Grid Representation",
    1025: "Projection Parameters (except Lambert CC)",
    1026: "Projection Parameters (Lambert CC)",
    1027: "Projection Parameters (Oblique Mercator)",

    # Miscellaneous
    1029: "Unicode Text String",
    1030: "GPS Network RTK Residual",
    1031: "GLONASS Network RTK Residual",
    1032: "Physical Reference Station Position",
    1033: "Receiver & Antenna Descriptors",
    1034: "GPS Network FKP Gradient",
    1035: "GLONASS Network FKP Gradient",

    # GLONASS Code-Phase Bias
    1037: "GLONASS L1 Code-Phase Bias",
    1038: "GLONASS L2 Code-Phase Bias",
    1039: "GLONASS Combined L1/L2 Code-Phase Bias",

    # Additional Ephemerides
    1042: "BDS Satellite Ephemerides",
    1044: "QZSS Satellite Ephemerides",
    1045: "Galileo F/NAV Satellite Ephemerides",
    1046: "Galileo I/NAV Satellite Ephemerides",

    # GPS SSR Corrections
    1057: "GPS SSR Orbit Correction",
    1058: "GPS SSR Clock Correction",
    1059: "GPS SSR Code Bias",
    1060: "GPS SSR Combined Orbit & Clock",
    1061: "GPS SSR URA",
    1062: "GPS SSR High-Rate Clock",

    # GLONASS SSR Corrections
    1063: "GLONASS SSR Orbit Correction",
    1064: "GLONASS SSR Clock Correction",
    1065: "GLONASS SSR Code Bias",
    1066: "GLONASS SSR Combined Orbit & Clock",
    1067: "GLONASS SSR URA",
    1068: "GLONASS SSR High-Rate Clock",

    # GPS MSM (Multiple Signal Messages)
    1071: "GPS MSM1",
    1072: "GPS MSM2",
    1073: "GPS MSM3",
    1074: "GPS MSM4",
    1075: "GPS MSM5",
    1076: "GPS MSM6",
    1077: "GPS MSM7",

    # GLONASS MSM
    1081: "GLONASS MSM1",
    1082: "GLONASS MSM2",
    1083: "GLONASS MSM3",
    1084: "GLONASS MSM4",
    1085: "GLONASS MSM5",
    1086: "GLONASS MSM6",
    1087: "GLONASS MSM7",

    # Galileo MSM
    1091: "Galileo MSM1",
    1092: "Galileo MSM2",
    1093: "Galileo MSM3",
    1094: "Galileo MSM4",
    1095: "Galileo MSM5",
    1096: "Galileo MSM6",
    1097: "Galileo MSM7",

    # SBAS MSM
    1101: "SBAS MSM1",
    1102: "SBAS MSM2",
    1103: "SBAS MSM3",
    1104: "SBAS MSM4",
    1105: "SBAS MSM5",
    1106: "SBAS MSM6",
    1107: "SBAS MSM7",

    # QZSS MSM
    1111: "QZSS MSM1",
    1112: "QZSS MSM2",
    1113: "QZSS MSM3",
    1114: "QZSS MSM4",
    1115: "QZSS MSM5",
    1116: "QZSS MSM6",
    1117: "QZSS MSM7",

    # BDS MSM
    1121: "BDS MSM1",
    1122: "BDS MSM2",
    1123: "BDS MSM3",
    1124: "BDS MSM4",
    1125: "BDS MSM5",
    1126: "BDS MSM6",
    1127: "BDS MSM7",

    # NavIC/IRNSS MSM
    1131: "NavIC MSM1",
    1132: "NavIC MSM2",
    1133: "NavIC MSM3",
    1134: "NavIC MSM4",
    1135: "NavIC MSM5",
    1136: "NavIC MSM6",
    1137: "NavIC MSM7",

    # Proprietary Messages
    4072: "u-blox Reference Station",
    4073: "u-blox Proprietary",
    4076: "IGS SSR",
}
