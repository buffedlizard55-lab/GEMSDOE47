# GEMS target population — established facts and unknowns

Reviewed 2026-10-06. Official requirements and geological hypotheses are separate.

## What is established

- The target is geological fault structures indicative of geothermal resources, not springs/wells themselves.
  [Official problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
- Supplied labels come from USGS Quaternary faults and INGENIOUS. Organizer experts labeled additional
  fault pixels; the region is spatially split into public/private test chunks. Participant scores do not
  identify a TIFF. One selected submission is evaluated in both prize rounds.
- Existing catalogue pixels are excluded from scoring in both rounds, per
  [staff clarification 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516).
  Off-catalogue does not necessarily mean distant from a known fault: new geometry can be near or far.
- Staff explicitly withholds test data sources, fault types and coverage in
  [thread 11527](https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527?print=true).
  Do not infer that hidden labels primarily use lidar or that winners use a particular architecture.
- Grid read from pinned mirrors: EPSG:32611, 100 m, width 3292 × height 3730; 5,167,373 footprint and
  60,988 catalogue pixels. These hashes prove mirror consistency, not organizer authentication.

## What does not follow

“New geometry may adjoin a known system” does **not** imply the hidden target is primarily a 0–300 m halo.
Nor does an incomplete catalogue mean every linear terrain/geophysical edge is tectonic. Roads, channels,
lithologic contacts, erosion and survey/resampling boundaries need explicit competing explanations.

A catalogue-supervised model may learn regional sampling and mapped-fault bias rather than missing-fault
physics. H47-C1 is a concrete example: it beats random on catalogue cores but fails the frozen pooled
terrain-control comparison and loses to random on the distant SGMC diagnostic. It is not promoted.

## Scientific next directions, not validated discoveries

Raw 1 m elevation could preserve narrow landforms missing in a coarse feature product; the public
[USGS 3DEP page](https://www.usgs.gov/3d-elevation-program) states products are free without use restrictions.
Exact tile bytes, footprint and the competition tile-link CSV remain unacquired here. Persistent step heights
can survive averaging; do not claim every metre-scale throw is attenuated by a universal percentage.

[Sare et al. 2019](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018JB016886) used ≤2 m topography
for scarp-template detection. C1's 100 m, four-direction bank is a heuristic adaptation, not a replication
or a morphologic age estimator. Its widths are sampling steps, with √2-longer diagonal spacing.
