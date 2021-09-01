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
    12,13, "1.24";
    13,14, "1.6";
    14,15, "1.11";
    15,16,"4.82";
    16,17,"1.6";
    17,18,"1.78";).


distance(S2, S1, D) :- distance(S1, S2, D).
%#show distance/3.

% Each manually specified distance corresponds to variable
% fixed at that value


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
    5, "5.0";
    6, "7.0").


%%% Sequence

% Time, Station, Station
leg(T, T, T + 1) :- T=0..17.
leg(T, 18 - (T - 18), 18 - (T - 17)) :- T=18..35.

error("Leg station isn't a station", S1) :- leg(_, S1, _), not station(S1).
error("Leg station isn't a station", S2) :- leg(_, _, S2), not station(S2).
error("Leg not continous", S1, S2) :- leg(_, S1, S2), |S1 - S2| != 1.
error("Leg not continous", T) :- leg(T, S1, S2), leg(T + 1, S3, S4), S2 != S3.
%#show leg/3.


%%% Generate

1{
    run_leg(X,leg(A,B,C)): participant(X)
}1 :- leg(A,B,C).
%#show run_leg/2.

% Who runs what index
run(X,T) :- run_leg(X, leg(T,_,_)).
#show run/2.

%%% Plan metrics
leg_count(X, C) :- C = #count{run(X, T): run(X, T), participant(X)}, participant(X).
#show leg_count/2.
:- leg_count(X, 0), participant(X).

leg_dist(T, D) :- leg(T, S1, S2), distance(S1, S2, D).
%#show leg_dist/2.

total_dist(X, T) :- T = #sum{D: distance(S1, S2, D), run_leg(X,leg(_,S1,S2)), participant(X)}, participant(X).
#show total_dist/2.

deviation(X, |G - T|) :- total_dist(X, T), preferred_distance(X, G), participant(X).
%#show deviation/2.


%%% Objectives

% Make people run the distance they want to run
#minimize {D: deviation(X, D), participant(X)}.



#show error/2.
#show error/3.

