MerbeinCAD v0.4 update
=======================
1. Save this ZIP in C:\MerbeinCAD\Updates and Extract All.
2. CLOSE MerbeinCAD.
3. Double-click Update_MerbeinCAD.bat in the extracted folder.
4. Open C:\MerbeinCAD\Application\launch_windows.bat to run.

NEW TOOLS — hover over toolbar pictures for tool names
- Trash can: click an entity to DELETE (also Select > Delete key).
- Trim (crossing lines): click the unwanted section of a LINE. Other drawing objects are cutting boundaries. When clicked between two boundaries, the line is split into two pieces.
- Extend (line and arrow): click near the end of a LINE to extend it to the nearest line or circle boundary. Only straight lines can currently be trimmed/extended; undo with Ctrl+Z.
- Two circles and tangent: click the two CIRCLE circumferences; up to four dashed common tangents appear. Click near the desired dashed line to create the tangent line. Green = external, amber = internal. Esc cancels.
- Rectangular array button (grid symbol): select ONE entity first with the arrow tool; enter rows, columns, horizontal and vertical spacing in mm. Original remains; copies use current entity's layer.
- Polar array (radial symbol): select ONE entity first; enter centre X,Y, item count including original, total sweep degrees. Full 360-degree array does not duplicate the last point; for partial sweep, the last item is at the final angle. Rotated rectangles become closed polylines.
- Print (printer symbol or File > Print / PDF): export a printable vector PDF in A4/A3, portrait/landscape. The drawing is FIT TO PAGE; it is NOT to physical 1:1 scale. PDF opens in your normal PDF application for printing.
- Existing endpoint, midpoint, centre, quadrant, tangent-from-point and intersection snap modes are retained.

Python 3.11+ and internet connection for first-time pip packages are needed.
The launch_windows.bat script installs ezdxf and reportlab automatically.
Please keep a backup of your drawing projects. This prototype has not yet been tested on Windows.

GitHub updates:
- Existing Help > Configure GitHub repository and Check for Updates remain.
- To publish this version, attach the ZIP as MerbeinCAD_Update.zip to a GitHub Release tagged v0.4 in your configured public repository.
- No GitHub repository or release has been created by this ZIP.
