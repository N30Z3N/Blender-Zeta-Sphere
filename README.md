**Disclaimer**: I'm not the original author just took this tool and updated with gemini 3.0 pro to be compatible with blender 5.0.

# Sculpt Tools for Blender

**Rapid Armature-to-Mesh Prototyping System**

**Sculpt Tools** is a streamlined Blender Add-on designed to accelerate the concept sculpting phase. It allows artists to "sketch" characters and forms using Armatures (Bones) and instantly convert them into water-tight, sculpt-ready meshes using either Skin Modifiers or Envelope Primitives.

It supports a non-destructive iterative workflow, allowing you to tweak bone positions and radii and update the generated mesh instantly.

---

## 📦 Installation

1. Download the `.py` file.
2. Open Blender.
3. Go to **Edit > Preferences > Add-ons**.
4. Click **Install...** and select the file.
5. Enable the checkbox for **Sculpt Tools**.

> **Note:** The script metadata indicates compatibility with Blender 5.0, but the API usage is compatible with Blender 3.x and 4.x.

---

## 📍 Location

Once installed, the tool is located in the **3D Viewport Header**.
Look for the **"Sculpt Tools"** popover button (usually near the top right of the viewport, near the Options/Gizmo toggles).

---

## 🛠️ Workflow Guide

### 1. Initialization
1. Click the **Sculpt Tools** menu in the header.
2. Select **Add Envelope**.
   * *This creates a specialized Armature set to 'Envelope' display mode.*
   * *It automatically enters **Edit Mode**.*

### 2. Sketching the Form
manipulate the bones to define the underlying structure of your character or object.
*   **Extrude:** Use `E` to create new limbs/segments.
*   **Scale Radius:** Use `Alt + S` to change the thickness of the bones.
    * *Critically, the tool reads the **Bone Radius** (Head/Tail) to determine the volume of the generated mesh.*

### 3. Conversion Methods
With the Armature selected, open the Sculpt Tools menu and choose a generation method:

#### A. The Skin Method (👤)
*   **Best for:** Organic characters, fingers, tree branches, limbs.
*   **How it works:** Generates a mesh with the **Skin Modifier**. It creates a clean quad-topology cage around the bones.
*   **Settings:**
    *   Uses **PreSubdivision** to smooth the input before skinning.
    *   Uses **Subdivision** for final smoothing.

#### B. The Envelope Method (spheres/cones) (🌐)
*   **Best for:** Blockouts, robot parts, muscular shapes using primitives.
*   **How it works:** Procedurally generates **UV Spheres** at bone joints and **Cones** spanning the bone lengths. It joins them into a single mesh.
*   **Settings:**
    *   Applies a **Bevel Modifier** to smooth intersections.
    *   Uses **Subdivision** for final smoothing.

---

## 🔄 The Iterative "Update" Workflow

One of the most powerful features of this tool is the ability to refine the shape after generation.

1. Generate your mesh using **Skin** or **Envelope**.
2. Notice the mesh is created, but the Armature remains selected.
3. **Move/Scale/Extrude** bones in Edit Mode to correct the proportions.
4. Open the Sculpt Tools menu.
5. Click the **Refresh Icon ( 🔄 )** next to the conversion button.
   * *This deletes the old mesh and regenerates a new one based on the updated bone positions/radii.*

---

## ⚙️ Parameters

| Setting | Description |
| :--- | :--- |
| **Subdivision** | The final subdivision level applied to the generated mesh (Viewport levels). |
| **PreSubdivision** | *(Skin Mode Only)* Subdivides the edge-graph before applying the Skin modifier. Higher values result in smoother bends but higher poly counts. |
| **Clean Limit** | Distance threshold for the "Remove Doubles" operation. Helps clean up overlapping geometry at joints. |

---

## ⌨️ Hotkeys & Tips

*   **Radius Control:** The thickness of the mesh is driven entirely by bone radius. Select a bone tail or head and press **`Alt+S`** to scale it.
*   **Context:** The tool automatically manages Object/Edit mode switching, but ensures you have the Armature selected before clicking Convert.
*   **Modifiers:** The generated meshes remain live (modifiers are not applied). You can manually tweak the Skin or Subsurf modifiers in the Modifier Properties panel after generation.

---

## 📝 Credits
*   **Original Author:** [Alfonso Annarumma](https://github.com/anfeo)
*   **Category:** Sculpting / Modeling
