from public_salaries.portals import socrata

# Each source file names its portal; every portal module offers read_year().
PORTALS = {"socrata": socrata}
