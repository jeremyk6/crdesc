# crdesc

**crdesc** is a python package that produces a textual description from a [crmodel](https://github.com/jeremyk6/crmodel) output.

This tool was developed and tested under Ubuntu 20.04.

## Dependencies

This tool depends on crmodel and [pyrealb](https://github.com/lapalme/pyrealb). You can install everything with pip:

```bash
pip3 install -r requirements.txt
````

## How to use

You can obtain a description of an intersection this way:

```bash
./main -c x y [-o output format]
```
With **x** and **y** the coordinates of the targeted intersection. Description will be outputed on stdout. You can also output the json and geojson of crmodel that will be completed with the description of each object.