### **1. Executive Summary**

This project will create an interactive web-based demonstration of the paper *"Vision-Only Gaussian Splatting for Collaborative Semantic Occupancy Prediction"*. The goal is to visually communicate the paper's core value proposition: that transmitting sparse 3D Gaussian primitives is significantly more bandwidth-efficient and effective for collaborative autonomous driving perception than traditional dense voxel methods.

The demo will feature a split-screen comparison allowing users to toggle between "Traditional Dense Voxels" and "Proposed Sparse Gaussians," manipulated independently in 3D space.

---

### **2. Technical Stack & Constraints**

* **Framework:** Angular (Latest Stable)
* **3D Engine:** Three.js (via `@types/three` or `angular-three` wrapper if preferred)
* **Hosting:** Vercel
* **Data Source:** **Self-contained.** All geometry, Gaussian parameters (mean, covariance, color, opacity), and voxel data must be procedurally generated or hard-coded within the repository. No external API calls or file loading from buckets.
* **Responsiveness:** Desktop-first, but viewable on mobile.

---

### **3. Functional Requirements**

#### **3.1. The Visualization Core (The "Hook")**

**Split-Screen Interface:** The viewport must be divided into two distinct 3D scenes (or one scene with a masking shader) as depicted in the generated wireframe.
**Left View (Baseline):** Represents "Dense Voxels" or "Planar Features".

**Right View (Ours):** Represents "Sparse 3D Semantic Gaussians".
* **Independent Manipulation:**
* User must be able to rotate (orbit), zoom, and pan **Left View** without affecting **Right View**, and vice versa.
* **Constraint:** Controls must not conflict (e.g., dragging the left side shouldn't rotate the right side).
* **Toggle/Slider Mechanism:** A UI slider or handle that allows the user to expand one view over the other, effectively comparing them side-by-side.

#### **3.2. Data Simulation & Accuracy**

* **Gaussian Primitives (Right View):**
* Must render ellipsoids defined by the paper's 5 parameters: Mean (), Scale (), Rotation (, quaternion), Opacity (), and Semantics ().
 
**Formula Compliance:** The rendering must visually respect Equation 7 in the paper: .

**Visual Style:** Primitives should be colored by semantic class (e.g., gray for road, red for cars, green for vegetation).
* **Dense Voxels (Left View):**
* Must render a grid of cubes representing the "dense" approach.
**Visual Style:** Semi-transparent blocks that clutter the view, representing the "high communication cost" referenced in the abstract.

#### **3.3. The "Bandwidth" Narrative**

* **Data Budget HUD:**
* Display a dynamic bar chart or progress bar.
* 
**State A (Voxels):** Show "Transmission Volume" at **100% (Overload)**.

**State B (Gaussians):** Show "Transmission Volume" at **~34.6%**.
* **Performance Metrics:**
* Display static text comparing accuracy: "Baseline mIoU" vs. "Ours (+1.9 mIoU)".
#### **3.4. Informational Content**

* **Summary Section:**
* A text section below the WebGL canvas summarizing the paper.
* 
**Key Message:** Focus on the "collaborative perception" aspect—how sharing Gaussians allows cars to see around corners (occlusion management).


* **Tone:** Technical but accessible, similar to the TGL demo website.



---

### **4. Visual Design Specifications**

* **Aesthetic:** Dark mode, technical/futuristic dashboard style (referencing the generated image).
* **Color Palette:**
* Background: Deep charcoal/black (`#121212`).
* Gaussians: Bright, distinct semantic colors (Red, Blue, Green, Yellow).
* Voxels: Muted, translucent blue/gray grid lines.
* UI Accents: Neon Green for "Efficient/Good," Alert Red for "Overload/Bad."
---

### **5. Implementation Roadmap (Angular + Three.js)**

#### **Phase 1: Project Setup**
1. Initialize Angular workspace.
2. Install Three.js and setup a basic `CanvasComponent`.
3. Configure Vercel deployment pipeline.

#### **Phase 2: The Data Generators (The "Hard-Coded" Part)**

* *Note: Since we cannot load external files, we need a TS service to generate the scene.*
* **`SceneGeneratorService`**:
* `generateEgoVehicle()`: Returns a group of meshes representing the main car.
* `generateStreetEnvironment()`: Returns static mesh data for roads.
* **`generateVoxels()`**: Returns a large array of positions for the "Bad" visualization (a dense grid).

**`generateGaussians()`**: Returns an array of objects `{ position, scale, rotation, color }` clustered *only* around the object surfaces (road, car), leaving air empty.


#### **Phase 3: The 3D Component**
* Create two `THREE.Scene` instances (or use viewport scissoring in one renderer).
* Implement `OrbitControls` for each view, ensuring event listeners are bound to specific `div` containers to prevent control bleeding.
* Implement the "Gaussian Splat" shader or mesh instancing to render thousands of ellipsoids efficiently.

#### **Phase 4: UI & Integration**
* Build the overlay HUD (Bandwidth bars).
* Add the "Summary" text section.
* Polish the visual transitions.

---

### **6. Success Criteria**
**Visual Fidelity:** The Gaussian view looks significantly "cleaner" and more object-centric than the Voxel view.
* **Performance:** The demo runs at 60fps on a standard laptop.
* **Message Clarity:** A user understands within 10 seconds that "Gaussians = Less Data & Better View."