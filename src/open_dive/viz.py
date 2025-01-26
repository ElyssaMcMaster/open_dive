import nibabel as nib
import numpy as np
from dipy.viz import window, actor
from fury.actor import slicer
from fury.colormap import colormap_lookup_table
import vtk
import matplotlib.pyplot as plt
from matplotlib import cm  # Importing Matplotlib colormap module

def plot_nifti(
    nifti_path,
    data_slice="m",
    orientation="axial",
    size=(600, 400),
    value_range=None,
    radiological=True,
    save_path=None,
    interactive=True,
    scalar_colorbar=True,
    tractography=None,
    tractography_colormap=None,
    volume_idx=None,
    **kwargs,
):
    """Create a 2D rendering of a NIFTI slice."""
    # Load the data and convert to RAS
    nifti = nib.load(nifti_path)
    nifti = nib.as_closest_canonical(nifti)
    data = nifti.get_fdata()

    if len(data.shape) == 4:
        if volume_idx is None:
            raise ValueError(
                "Input is a 4D image but no volume index specified. "
                "Please provide a volume_idx parameter to select which 3D volume to display."
            )
        if not 0 <= volume_idx < data.shape[3]:
            raise ValueError(
                f"volume_idx {volume_idx} is out of bounds for image with {data.shape[3]} volumes"
            )
        data = data[..., volume_idx]
    elif len(data.shape) != 3:
        raise ValueError(
            f"Expected 3D or 4D image, but got image with {len(data.shape)} dimensions"
        )

    # Get the data and affine
    affine = nifti.affine

    # value range
    if value_range is None:
        value_range = [np.min(data), np.max(data)]
    else:
        value_range = [value_range[0], value_range[1]]

    if radiological and orientation == "axial":
        data = np.flip(data, axis=0)

    # Set up slicer and window
    slice_actor = slicer(data, affine=affine, value_range=value_range, **kwargs)
    scene = window.Scene()
    scene.add(slice_actor)

    # Get slice if not defined
    if orientation == "axial":
        data_slice = data.shape[2] // 2 if data_slice == "m" else data_slice
        slice_actor.display_extent(
            0, data.shape[0], 0, data.shape[1], data_slice, data_slice
        )

        camera_pos = (0, 0, 1)
        camera_up = (0, 1, 0)
    elif orientation == "coronal":
        data_slice = data.shape[1] // 2 if data_slice == "m" else data_slice
        slice_actor.display_extent(
            0, data.shape[0], data_slice, data_slice, 0, data.shape[2]
        )

        camera_pos = (0, 1, 0)
        camera_up = (0, 0, 1)
    elif orientation == "sagittal":
        data_slice = data.shape[0] // 2 if data_slice == "m" else data_slice
        slice_actor.display_extent(
            data_slice, data_slice, 0, data.shape[1], 0, data.shape[2]
        )

        camera_pos = (1, 0, 0)
        camera_up = (0, 0, 1)
    camera_focal = (0, 0, 0)

    # Apply colorbar
    if scalar_colorbar:
        # Create a grayscale colormap (from black to white)
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(256)  # Full grayscale (256 levels)
        lut.Build()  # Initialize the LUT
        
        for i in range(256):
            lut.SetTableValue(i, i / 255.0, i / 255.0, i / 255.0, 1)  # Grayscale colors
        lut.SetRange(value_range[0], value_range[1])  # This defines the grayscale range explicitly

        # Create the scalar bar (colorbar)
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetLookupTable(lut)  # Attach the grayscale LUT
        scalar_bar.SetLabelFormat("%.0f")  # Integer labels (0, 1, 2, ... 255)
        scalar_bar.SetPosition(0.8, 0.1)  # Position of the colorbar
        scalar_bar.SetHeight(0.5)  # Adjust height (increase size)
        scalar_bar.SetWidth(0.1)   # Adjust width (increase size)

        # Add the scalar bar to the scene
        scene.add(scalar_bar)

    # Add tractography
    if tractography is not None:
        streamlines = nib.streamlines.load(tractography).streamlines
        stream_actor = actor.line(streamlines, colors=None)
        scene.add(stream_actor)
        


            




    # Set up camera
    scene.set_camera(position=camera_pos, focal_point=camera_focal, view_up=camera_up)

    # Show the scene
    if save_path:
        window.record(scene=scene, out_path=save_path, size=size, reset_camera=True)

    if interactive:
        window.show(scene, size=size, reset_camera=True)






