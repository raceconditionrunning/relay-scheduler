#program base.
%% Stations
station(0..18).
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
    13, "Colombia City";
    14, "Othello";
    15, "Rainier Beach";
    16, "Tukwila International Blvd";
    17, "SeaTac/Airport";
    18, "Angle Lake";
     ).

distance(
    0,1, "2.25";
    1,2, "1.23";
    2,3, "1.04";
    3,4, "2.78";
    4,5, "0.96";
    5,6, "0.37";
    6,7, "0.49";
    7,8, "0.35";
    8,9, "0.6";
    9,10, "0.68";
    10,11, "1.31";
    11,12, "0.82";
    13,14, "1.24";
    14,15, "1.6";
    15,16, "1.11";
    16,17,"4.82";
    17,18,"1.6";).

forward(0..17, 1..18).
forward(1..18, 0..17).

%% Participants
participant(0..6).
name(0, "Nick").
name(1, "Ellis").
name(2, "Chandra").
name(3, "Zach").
name(4, "Yuxuan").
name(5, "Max").
name(6, "Ewin").

%% Preferences 

% Person, Station
nearest_station(
    0, 2;
    1, 4;
    2, 12;
    3, 14;
    4, 2;
    5, 3,
    6, 1).

preferred_distance(
    0, "10.0";
    1, "11.0";
    2, "6.0";
    3, "6.0";
    4, "5.0";
    5, "5.0").


%%% Sequence

% Time, Station, Station
leg(T, T, T + 1) :- T=0..17.
leg(T, 18 - (T - 18), 18 - (T - 17)) :- T=18..35.

error("Leg station isn't a station", S1) :- leg(_, S1, _), not station(S1).
error("Leg station isn't a station", S2) :- leg(_, _, S2), not station(S2).
error("Leg not continous", S1, S2) :- leg(_, S1, S2), |S1 - S2| != 1.
error("Leg not continous", T) :- leg(T, S1, S2), leg(T + 1, S3, S4), S2 != S3.
%#show leg/3.



1{
    run(X,leg(A,B,C)): participant(X)
}1 :- leg(A,B,C).


&sum{D:distance(B, C, D), run(X, leg(A,B,C))} < 10 :- participant(X).


%%%%%%%%%%%%%%%%%%%%%%% Instance


#show run/2.
#show error/2.
#show error/3.