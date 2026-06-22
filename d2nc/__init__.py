"""d2nc — spike CLI: convert a Bruker .d to NetCDF via a local or cloud backend.

This is a thin front door over the existing converter:
  * local backend  -> in-process ``src/extract.py::extract_data``
  * cloud backend  -> direct ECS run_task on the deployed ``conversion-service``

See project-management/dot-d-to-nc-component-design.md for the design intent.
"""

__version__ = "0.0.1-spike"
