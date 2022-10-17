s_name(
   18, "Northgate";
   17, "Roosevelt";
   16, "U-District";
   15, "University of Washington";
   14, "Capitol Hill";
   13, "Westlake";
   12, "University Street";
   11, "Pioneer Square";
   10, "International District/Chinatown";
    9, "Stadium";
    8, "SODO";
    7, "Beacon Hill";
    6, "Mount Baker";
    5, "Columbia City";
    4, "Othello";
    3, "Rainier Beach";
    2, "Tukwila International Blvd";
    1, "SeaTac/Airport";
    0, "Angle Lake"
).

station(X) :- s_name(X, _).     

distance(
    17,18, "2.40";
    16,17, "1.41";
    15,16, "1.22";
    14,15, "2.82";
    13,14, "1.10";
    12,13, "0.98";
    11,12, "0.49";
    10,11, "0.30";
    9,10, "0.73";
    8,9, "0.68";
    7,8, "1.39";
    6,7, "0.81";
    5,6, "1.28";
    4,5, "1.61";
    3,4, "1.09";
    2,3,"6.64";
    1,2,"1.50";
    0,1,"1.74"
).

distance(S2, S1, D) :- distance(S1, S2, D).

ascent(
    17,18, 263; 18,17, 234;
    16,17, 120; 17,16, 73;
    15,16, 176; 16,15, 73;
    14,15, 252; 15,14, 514;
    13,14, 245; 14,13, 47;
    12,13, 97; 13,12, 92;
    11,12, 66; 12,11, 3;
    10,11, 44; 11,10, 27;
    9,10, 47; 10,9, 22;
    8,9, 15; 9,8, 12;
    7,8, 15; 8,7, 288;
    6,7, 257; 7,6, 17;
    5,6, 26; 6,5, 106;
    4,5, 39; 5,4, 32;
    3,4, 82; 4,3, 20;
    2,3, 600; 3,2, 850;
    1,2, 97; 2,1, 118;
    0,1, 55; 1,0, 113
).

stroller_traversible(
    15,16;
    16,17
).

stroller_traversible(End, Start) :- stroller_traversible(Start, End).
