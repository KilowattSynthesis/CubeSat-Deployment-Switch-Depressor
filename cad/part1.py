import os
from pathlib import Path

import build123d as bd

from loguru import logger


if os.getenv("CI"):

    def show(*args: object) -> bd.Part:
        """Do nothing (dummy function) to skip showing the CAD model in CI."""
        logger.info(f"Skipping show({args}) in CI")
        return args[0]
else:
    import ocp_vscode

    def show(*args: object) -> bd.Part:
        """Show the CAD model in the CAD viewer."""
        ocp_vscode.show(*args)
        return args[0]


# Constants
sat_width = 100 + 0.7
solar_panel_thickness = 10  # Max allowable is 6mm, iirc.
rails_width = 7 + 0.5

stand_length_z = 50

bottom_thickness_z = 2
side_thickness_xy = 2

bottom_hole_diameter = 100 + (2 * solar_panel_thickness) - 10


# Calculated values.
total_stand_width = (
    sat_width + (2 * solar_panel_thickness) + (2 * side_thickness_xy)
)
total_solar_panel_width = sat_width - (2 * rails_width)


def validate():
    """Raise if variables are not valid."""
    pass


def make_stand():
    part = bd.Part() + bd.Box(
        total_stand_width,
        total_stand_width,
        stand_length_z + bottom_thickness_z,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    )

    # Round the corners.
    part = part.fillet(
        radius=20,
        edge_list=part.edges().filter_by(bd.Axis.Z),
    )

    # Remove the main cubesat body.
    part -= bd.Box(
        sat_width,
        sat_width,
        stand_length_z,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    ).translate((0, 0, bottom_thickness_z))

    # Remove the solar panels.
    for rot in (0, 90):
        part -= (
            bd.Box(
                total_solar_panel_width,
                sat_width + (2 * solar_panel_thickness),
                stand_length_z,
                align=(
                    bd.Align.CENTER,
                    bd.Align.CENTER,
                    bd.Align.MIN,
                ),
            )
            .rotate(axis=bd.Axis.Z, angle=rot)
            .translate((0, 0, bottom_thickness_z))
        )

    # Remove the big bottom hole.
    part -= bd.Cylinder(
        radius=bottom_hole_diameter / 2,
        height=1000,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    )

    return part


if __name__ == "__main__":
    validate()

    parts = {
        "stand": make_stand(),
    }

    logger.info("Showing CAD model(s)")
    show(parts["stand"])

    (export_folder := Path(__file__).parent.with_name("build")).mkdir(
        exist_ok=True
    )
    for name, part in parts.items():
        assert isinstance(part, bd.Part), f"{name} is not a Part"
        # assert part.is_manifold is True, f"{name} is not manifold"

        bd.export_stl(part, str(export_folder / f"{name}.stl"))
        bd.export_step(part, str(export_folder / f"{name}.step"))
