#
# Copyright 2017-2021 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors:
#   Alessandro Amici - B-Open - https://bopen.eu
#

import os.path
import typing as T

import click

# NOTE: imports are executed inside functions so missing dependencies don't break all commands


@click.group()
def cfgrib_cli() -> None:
    pass


@cfgrib_cli.command("selfcheck")
def selfcheck() -> None:
    from .messages import eccodes_version

    print("Found: ecCodes v%s." % eccodes_version)
    print("Your system is ready.")


@cfgrib_cli.command("to_netcdf")
@click.argument("inpaths", nargs=-1)
@click.option("--outpath", "-o", default=None, help="Filename of the output netcdf file.")
@click.option(
    "--cdm", "-c", default=None, help="Coordinate model to translate the grib coordinates to."
)
@click.option(
    "--engine", "-e", default="cfgrib", help="xarray engine to use in xarray.open_dataset."
)
@click.option(
    "--backend-kwargs-json",
    "-b",
    default=None,
    help=(
        "Backend kwargs used in xarray.open_dataset."
        "Can either be a JSON format string or "
        "the path to JSON file"
    ),
)
def to_netcdf(inpaths, outpath, cdm, engine, backend_kwargs_json):
    # type: (T.List[str], str, str, str, str) -> None
    import xarray as xr

    # NOTE: noop if no input argument
    if len(inpaths) == 0:
        return

    if not outpath:
        outpath = os.path.splitext(inpaths[0])[0] + ".nc"

    if backend_kwargs_json is not None:
        import json  # only import if used

        try:
            # Assume a json format string
            backend_kwargs = json.loads(backend_kwargs_json)
        except json.JSONDecodeError:
            # Then a json file
            with open(backend_kwargs_json, "r") as f:
                backend_kwargs_json = json.load(f)
    else:
        backend_kwargs = {}

    if len(inpaths) == 1:
        # avoid to depend on dask when passing only one file
        ds = xr.open_dataset(
            inpaths[0], engine=engine, backend_kwargs=backend_kwargs,
        )  # type: ignore
    else:
        ds = xr.open_mfdataset(
            inpaths, engine=engine, combine="by_coords", backend_kwargs=backend_kwargs,
        )  # type: ignore

    if cdm:
        import cf2cdm  # only import if used

        coord_model = getattr(cf2cdm, cdm)
        ds = cf2cdm.translate_coords(ds, coord_model=coord_model)

    ds.to_netcdf(outpath)


@cfgrib_cli.command("dump")
@click.argument("inpaths", nargs=-1)
@click.option("--variable", "-v", default=None)
@click.option("--cdm", "-c", default=None)
@click.option("--engine", "-e", default="cfgrib")
def dump(inpaths, variable, cdm, engine):
    # type: (T.List[str], str, str, str) -> None
    import xarray as xr

    import cf2cdm

    # NOTE: noop if no input argument
    if len(inpaths) == 0:
        return

    if len(inpaths) == 1:
        # avoid to depend on dask when passing only one file
        ds = xr.open_dataset(inpaths[0], engine=engine)  # type: ignore
    else:
        ds = xr.open_mfdataset(inpaths, engine=engine, combine="by_coords")  # type: ignore

    if cdm:
        coord_model = getattr(cf2cdm, cdm)
        ds = cf2cdm.translate_coords(ds, coord_model=coord_model)

    if variable:
        ds_or_da = ds[variable]
    else:
        ds_or_da = ds

    print(ds_or_da)


if __name__ == "__main__":  # pragma: no cover
    cfgrib_cli()
