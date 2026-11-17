# MerbeinCAD v0.7 — engineering CAD prototype

2D sketch drawing in millimetres plus a new 3D wireframe viewer.

## Changes from v0.6
- Hover over toolbar icons: tooltips now work without being replaced by the status-bar bindings.
- Dimension tool: pick the two measured points, then a third point to place the dimension line off the feature. Existing dimensions default to their old position; select + double-click to edit the `offset` value in millimetres.
- Layers > Edit current layer colour / linetype: continuous, centre, hidden, dash-dot. Styles persist in .mrcad files and DXF export.
- File > Save as DXF; File > Save as STEP; 3D > Add point / Extrude / Revolve / 3D View.
- Extrude / revolve: select one closed rectangle, circle or polyline. Revolve axis uses X or Y axis through origin; ensure profile does not cross revolution axis.
- 3D View: left-drag to orbit, Shift-drag or middle-drag to pan, wheel to zoom. Preview is a WIREframe, not a shaded parametric B-rep model.
- Genuine Merbein Robotics wordmark taken from supplied artwork used in earlier GCS application.

## Dependencies / STEP
Run `launch_windows.bat` for normal 2D work. `requirements.txt` installs ezdxf, Pillow and reportlab.
STEP uses CadQuery as a separate, optional dependency. On Windows run `Install_3D_STEP.bat` (a compatible Python distribution is required). Without CadQuery, the 3D preview works but STEP export shows a clear error.
STEP export writes independent solids; it does not fuse overlapping geometry, cut holes, fillet 3D edges or include point3d annotations.

## Windows installation
First installation: extract ZIP, open `Application`, run `Install_MerbeinCAD.bat`.
Existing installations: publish this package as release asset `MerbeinCAD_Update.zip` and use Help > Check for Updates, or run `Update_MerbeinCAD.bat` after closing the app.
The external updater waits for the old CAD process to exit and backs up Application. Never install with files open in the Application folder.

## Compatibility
Older v0.1–v0.6 `.mrcad` files can be loaded. Project files remain in Projects, not Application. 3D entities and layer styles require v0.7 or later.
