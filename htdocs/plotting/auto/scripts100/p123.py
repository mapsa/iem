import psycopg2
from pyiem.network import Table as NetworkTable
from pandas.io.sql import read_sql
import datetime
import numpy as np


def get_description():
    """ Return a dict describing how to call this plotter """
    d = dict()
    d['data'] = True
    d['report'] = True
    d['description'] = """ """
    d['arguments'] = [
        dict(type='station', name='station', default='IA2203',
             label='Select Station'),
    ]
    return d


def wrap(cnt, s=None):
    if cnt > 0:
        return s or cnt
    else:
        return ""


def contiguous_regions(condition):
    # http://stackoverflow.com/questions/4494404
    """Finds contiguous True regions of the boolean array "condition". Returns
    a 2D array where the first column is the start index of the region and the
    second column is the end index."""

    # Find the indicies of changes in "condition"
    # d = np.diff(condition)
    d = np.subtract(condition[1:], condition[:-1], dtype=np.float)
    idx, = d.nonzero()

    # We need to start things after the change in "condition". Therefore,
    # we'll shift the index by 1 to the right.
    idx += 1

    if condition[0]:
        # If the start of condition is True prepend a 0
        idx = np.r_[0, idx]

    if condition[-1]:
        # If the end of condition is True, append the length of the array
        idx = np.r_[idx, condition.size]  # Edit

    # Reshape the result into two columns
    idx.shape = (-1, 2)
    return idx


def plotter(fdict):
    """ Go """
    import matplotlib
    matplotlib.use('agg')
    pgconn = psycopg2.connect(database='coop', host='iemdb', user='nobody')
    cursor = pgconn.cursor()

    station = fdict.get('station', 'IA0200')

    table = "alldata_%s" % (station[:2], )
    nt = NetworkTable("%sCLIMATE" % (station[:2], ))
    res = """\
# IEM Climodat http://mesonet.agron.iastate.edu/climodat/
# Report Generated: %s
# Climate Record: %s -> %s
# Site Information: [%s] %s
# Contact Information: Daryl Herzmann akrherz@iastate.edu 515.294.5978
# First occurance of record consecutive number of days
# above or below a temperature threshold
""" % (datetime.date.today().strftime("%d %b %Y"),
       nt.sts[station]['archive_begin'].date(), datetime.date.today(), station,
       nt.sts[station]['name'])
    res += "#   %-27s %-27s  %-27s %-27s\n" % (" Low Cooler Than",
                                               " Low Warmer Than",
                                               " High Cooler Than",
                                               " High Warmer Than")
    res += "%3s %5s %10s %10s %5s %10s %10s  %5s %10s %10s %5s %10s %10s\n" % (
      'TMP', 'DAYS', 'BEGIN DATE', 'END DATE',
      'DAYS', 'BEGIN DATE', 'END DATE',
      'DAYS', 'BEGIN DATE', 'END DATE',
      'DAYS', 'BEGIN DATE', 'END DATE')

    cursor.execute("""SELECT high, low from """+table+"""
    WHERE station = %s and day >= '1900-01-01' ORDER by day ASC
    """, (station, ))
    highs = np.zeros((cursor.rowcount,), 'f')
    lows = np.zeros((cursor.rowcount,), 'f')
    for i, row in enumerate(cursor):
        highs[i] = row[0]
        lows[i] = row[1]

    startyear = max([1900, nt.sts[station]['archive_begin'].year])
    for thres in range(-20, 101, 2):
        condition = lows < thres
        max_bl = 0
        max_bl_ts = datetime.date.today()
        for start, stop in contiguous_regions(condition):
            if (stop - start) > max_bl:
                max_bl = int(stop - start)
                max_bl_ts = datetime.date(startyear,
                                          1, 1) + datetime.timedelta(
                                                        days=int(stop))
        condition = lows >= thres
        max_al = 0
        max_al_ts = datetime.date.today()
        for start, stop in contiguous_regions(condition):
            if (stop - start) > max_al:
                max_al = int(stop - start)
                max_al_ts = datetime.date(startyear,
                            1, 1) + datetime.timedelta(days=int(stop))
        condition = highs < thres
        max_bh = 0
        max_bh_ts = datetime.date.today()
        for start, stop in contiguous_regions(condition):
            if (stop - start) > max_bh:
                max_bh = int(stop - start)
                max_bh_ts = datetime.date(startyear,
                            1, 1) + datetime.timedelta(days=int(stop))
        condition = highs >= thres
        max_ah = 0
        max_ah_ts = datetime.date.today()
        for start, stop in contiguous_regions(condition):
            if (stop - start) > max_ah:
                max_ah = int(stop - start)
                max_ah_ts = datetime.date(startyear,
                                          1, 1) + datetime.timedelta(
                                                        days=int(stop))

        res += ("%3i %5s %10s %10s %5s %10s %10s  "
                "%5s %10s %10s %5s %10s %10s\n"
                ) % (thres,
                        wrap(max_bl),
                        wrap(max_bl, (max_bl_ts -
                                datetime.timedelta(days=max_bl)).strftime("%m/%d/%Y")), 
                        wrap(max_bl, max_bl_ts.strftime("%m/%d/%Y") ),
                    
                        wrap(max_al),
                        wrap(max_al, (max_al_ts -
                                datetime.timedelta(days=max_al)).strftime("%m/%d/%Y")), 
                        wrap(max_al, max_al_ts.strftime("%m/%d/%Y") ),
                    
                        wrap(max_bh),
                        wrap(max_bh, (max_bh_ts -
                                datetime.timedelta(days=max_bh)).strftime("%m/%d/%Y")), 
                        wrap(max_bh, max_bh_ts.strftime("%m/%d/%Y") ),
                    
                        wrap(max_ah),
                        wrap(max_ah, (max_ah_ts -
                                datetime.timedelta(days=max_ah)).strftime("%m/%d/%Y")), 
                        wrap(max_ah, max_ah_ts.strftime("%m/%d/%Y")))


    return None, None, res

if __name__ == '__main__':
    plotter(dict())