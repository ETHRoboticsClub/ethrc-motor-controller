<p align="center" width="100%">
  <img alt="Logo" width="33%" src="Logos/ethrc_logo_black.png">
</p>

<h1 align="center">${BOARD_NAME}</h1>

<p align="center" width="100%">
  <a href="${GIT_URL}/actions/workflows/ci.yaml">
    <img alt="CI Badge" src="${GIT_URL}/actions/workflows/ci.yaml/badge.svg?branch=">
  </a>
</p>

***

<p align="center">
  <img alt="3D Top Angled" src="${png_3d_viewer_angled_top_outpath}" width="45%">
&nbsp; &nbsp; &nbsp; &nbsp;
  <img alt="3D Bottom Angled" src="${png_3d_viewer_angled_bottom_outpath}" width="45%">
</p>

***

## SPECIFICATIONS

| Parameter | ETHRC Motor Controller v1.0| 
| --- | --- |
| Voltage Input | 33 - 58.8V |
| Peak Electrical Power | TBD |
| Mass | TBD |
| Peak Phase Current | TBD |
| Communication | EtherCat, 5Mbps CAN-FD and SWD interface |
| Cooling | TBD|
| Positioning | 1x Onboard 14-bit Encoder and one external encoder |
| Control rate | TBD |
| PWM Switching Rate | TBD |
| MCU | STM32G474 |
| Dimensions | ${bb_w_mm} × ${bb_h_mm} mm |

***

## DIRECTORY STRUCTURE

    .
    ├─ Computations       # Misc calculations
    ├─ DXF_SVG            # Vector graphics
    ├─ HTML               # HTML files for generated webpage
    ├─ Images             # Pictures and renders
    │
    ├─ kibot_resources    # External resources for KiBot
    │  ├─ colors          # Color theme for KiCad
    │  ├─ fonts           # Fonts used in the project
    │  ├─ scripts         # External scripts used with KiBot
    │  └─ templates       # Templates for KiBot generated reports
    │
    ├─ kibot_yaml         # KiBot YAML config files
    ├─ KiRI               # KiRI (PCB diff viewer) files
    │
    ├─ lib                # KiCad footprint and symbol libraries
    │  ├─ 3d_models       # Component 3D models
    │  ├─ lib_fp          # Footprint libraries
    │  └─ lib_sym         # Symbol libraries
    │
    ├─ Logos              # Logos
    │
    ├─ Manufacturing      # Assembly and fabrication documents
    │  ├─ Assembly        # Assembly documents (BoM, pos, notes)
    │  │
    │  └─ Fabrication     # Fabrication documents (ZIP, notes)
    │     ├─ Drill Tables # CSV drill tables
    │     └─ Gerbers      # Gerbers
    │
    ├─ Report             # Reports for ERC/DRC
    ├─ Schematic          # PDF of schematic
    ├─ Templates          # Title block templates
    ├─ Testing
    │  └─ Testpoints      # Testpoints tables      
    │
    └─ Variants           # Outputs for assembly variants

***

## FIRMWARE


***

## CREDITS

Schematic is largely inspired by the moteus controllers designed by Josh Pieper and amulet motion controller designed by Vincent Nguyen. They were modified to meet our own specifications. The CI/CD workflow and the templates for this KiCad 9.0 project was forked from https://github.com/nguyen-v/KDT_Hierarchical_KiBot created by Vincent Nguyen.
***

## PHOTOS
