from enum import Enum


class JEWISH_MONTHS(Enum):
    nissan = 1
    iyar = 2
    sivan = 3
    tammuz = 4
    av = 5
    elul = 6
    tishrei = 7
    cheshvan = 8
    kislev = 9
    teves = 10
    shevat = 11
    adar = 12
    adar_ii = 13


class SIGNIFICANT_DAYS(Enum):
    erev_rosh_hashana = 1
    rosh_hashana = 2
    tzom_gedalyah = 3
    erev_yom_kippur = 4
    yom_kippur = 5
    erev_succos = 6
    succos = 7
    chol_hamoed_succos = 8
    hoshana_rabbah = 9
    shemini_atzeres = 10
    simchas_torah = 11
    chanukah = 12
    tenth_of_teves = 13
    tu_beshvat = 14
    taanis_esther = 15
    purim = 16
    shushan_purim = 17
    purim_katan = 18
    shushan_purim_katan = 19
    erev_pesach = 20
    pesach = 21
    chol_hamoed_pesach = 22
    pesach_sheni = 23
    lag_baomer = 24
    erev_shavuos = 25
    shavuos = 26
    seventeen_of_tammuz = 27
    tisha_beav = 28
    tu_beav = 29
    yom_hashoah = 30
    yom_hazikaron = 31
    yom_haatzmaut = 32
    yom_yerushalayim = 33


class SIGNIFICANT_SHABBOS(Enum):
    parshas_hachodesh = 1
    shabbos_hagadol = 2
    shabbos_shuva = 3
    parshas_shekalim = 4
    parshas_zachor = 5
    parshas_parah = 6


class CHESHVAN_KISLEV_KEVIAH(Enum):
    chaseirim = 1
    kesidran = 2
    shelaimim = 3
