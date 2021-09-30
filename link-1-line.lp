s_name(
    0, "Northgate";
    1, "Roosevelt";
    2, "U-District";
    3, "University of Washington";
    4, "Capitol Hill";
    5, "Westlake";
    6, "University Street";
    7, "Pioneer Square";
    8, "International District/Chinatown";
    9, "Stadium";
    10, "SODO";
    11, "Beacon Hill";
    12, "Mount Baker";
    13, "Columbia City";
    14, "Othello";
    15, "Rainier Beach";
    16, "Tukwila International Blvd";
    17, "SeaTac/Airport";
    18, "Angle Lake"
).

station(X) :- s_name(X, _).     

distance(
    0,1, "2.40";
    1,2, "1.38";
    2,3, "1.09";
    3,4, "2.78";
    4,5, "0.96";
    %5,6, "0.37";
    5,6, "1.05";
    6,7, "0.49";
    7,8, "0.35";
    8,9, "0.75";
    9,10, "0.68";
    10,11, "1.31";
    11,12, "0.82";
    12,13, "1.24";
    13,14, "1.6";
    14,15, "1.11";
    15,16,"6.63";
    16,17,"1.48";
    17,18,"1.78"
).

distance(S2, S1, D) :- distance(S1, S2, D).

climbing(
    0,1, 236; 1,0, 261;
    1,2, 68; 2,1, 111;
    2,3, 48; 3,2, 161;
    3,4, 549; 4,3, 288;
    4,5, 65; 5,4, 274;
    %5,6, 14; 6,5, 16;
    5,6, 103; 6,5, 79;
    6,7, 4; 7,6, 54;
    7,8, 51; 8,7, 25;
    8,9, 7; 9,8, 33;
    9,10, 10; 10,9, 12;
    10,11, 283; 11,10, 11;
    11,12, 12; 12,11, 251;
    12,13, 103; 13,12, 23;
    13,14, 27; 14,13, 37;
    14,15, 15; 15,14, 74;
    15,16, 850; 16,15, 590;
    16,17, 128; 17,16, 105;
    17,18, 105; 18,17, 47
).

stroller_traversible(
    1,2;
    2,3
).

stroller_traversible(End, Start) :- stroller_traversible(Start, End).
