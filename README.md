# Blender Cloud Renderer for Google Colab

Render Blender scenes on a Google Colab GPU using your own Google Drive.

- Supports Eevee and Cycles.
- Renders still images or animation frames.
- Supports Blender 3.6, 4.0-4.5, and 5.0-5.2.
- Uses the Google account authorized by each user.

## Open in Colab

[Launch the renderer](https://colab.research.google.com/github/JonesthemBones/Google-Colab-Blender-Renderer/blob/main/notebooks/Blender_Cloud_Renderer.ipynb)

- Set the runtime to **GPU**.
- Run the notebook from top to bottom.
- Authorize your own Google Drive when prompted.
- Upload your `.blend` file to `MyDrive/BlenderCloudRenderer/blend_files/`.
- Choose the Blender version, render engine, and render mode.
- Find results in `MyDrive/BlenderCloudRenderer/output/`.

On first use, the notebook creates this folder in your Drive:

```text
BlenderCloudRenderer/
- config.json
- blend_files/
- output/
```

The notebook does not use the publisher's Drive.

## Configuration

The default file is `config.json`. Common settings are:

- `drive.blend_filename`: your `.blend` filename. Default: `scene.blend`.
- `drive.output_subfolder`: folder for the render output.
- `render.engine`: `cycles`, `blender_eevee`, or `eevee_next`.
- `render.mode`: `still` or `animation`.
- `render.samples`: render samples.
- `blender.major_minor`: Blender version, such as `4.5` or `5.2`.

For animation, set `frame_start`, `frame_end`, and `frame_step`. Frames are saved
as numbered PNG files.

## Local development

Requires Python 3. To regenerate the notebook after changing the source cells:

```text
python build_notebook.py
```

The generated notebook is `notebooks/Blender_Cloud_Renderer.ipynb`.

For local rendering, install Blender and add its executable to PATH. Then run:

```text
python run_local.py
```

Blender version downloads are defined in `cells/cell_02_blender.py`.

## License

This project is licensed under the GNU General Public License v3.0.
See [LICENSE](LICENSE) for details.

## Publishing updates

- Regenerate the notebook with `python build_notebook.py`.
- Commit the source and generated notebook.
- Push to GitHub.
- Share the Colab link above.
