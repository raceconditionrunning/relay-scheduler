% Format: From Angle Lake to Northgate
leg(T, T, T + 1) :- T=0..17.

%%% Event constraints

:- leg_count(X, 0), participant(X).
:- C != 2, exchange_count(X, C), participant(X).
:- C < 1, lead_count(T, C), leg_time(T).

% Atleast 2 people on each leg
:- C < 2, leg_coverage(T, C), leg(T, _, _).


%%% Generate

% All combinations of paricipants running each leg
1{
   run_leg(X, leg(A,B,C)): participant(X)
}Count :- leg(A,B,C), participants(Count).


%%% Optimization Criteria

% Priority between objectives is lexicographic, largest number to lowest

% Try not to go too far over people's stated limits
#minimize {D @ 3: dist_overage(X, D), participant(X)}.

% Make people run the distance they want to run
#minimize {D @ 2: dist_deviation(X, D), participant(X)}.

#minimize {EndDeviation @ 1: end_deviation(X, EndDeviation), participant(X)}.

#minimize {Duration @ 0: duration(T, Duration), leg_time(T)}.

%%% Alternative criteria

% Make people run the pace they want to run
% #minimize {D @ 4: pace_deviation(X, T, D), participant(X), leg_time(T)}.
%:- Slack > 1000, pace_slack(X, T, Slack).

% Just get within half a mile for everyone
%:- Deviation > 50, dist_diff(X, Deviation).

% Print a key
objectives("dist overage","dist","commute", "duration").
#show objectives/4.


%%% Participant Preferences

preference(
%   Name           End  Dist    Pace
    "James",        14,  "8.0",  "9.5";
    "Nick",         14,  "13.0",  "9.0";
    "Lauren",       17,  "4.0",  "16.0";
    %"Lauren",       17,  "6.0",  "12.75";
    "Yuxuan",       17,  "8.0",  "12.0";
    "Maya",         17,  "3.0",  "10.0";
    "Chandra",      7,  "6.0", "10.0";
    "Dhruba",       14,  "8.0", "8.5";
    "Zach E.",      15,  "4.0", "8.5";
    "Justin",       15,  "6.0", "8.0";
    "Brett",        16,  "6.0",  "11.0";
    "Ethan",        14,  "6.0",  "9.5";
    "Zach T.",      6,   "4.0",  "11.0";
    "Ryan",         15,  "1.0",  "9.0";
    "Kevin",        13,  "3.0",  "12.0";
    "Edward",       18,  "4.0",  "10.0";
    "Marius",       16,  "6.0",  "9.0";
    "Ewin",         18,  "8.0",  "9.0";
    "Ellis",        14,  "13.0", "9.0";
).

% Designated as responsible for their legs
lead("Yuxuan"; "James"; "Chandra"; "Ellis"; "Zach"; "Nick"; "Edward").

participant(Name)
    :- preference(Name, Station, Distance, Pace).
preferred_pace(Name, Pace)
    :- preference(Name, Station, Distance, Pace).
nearest_station(Name, Station)
    :- preference(Name, Station, Distance, Pace).
preferred_distance(Name, Distance)
    :- preference(Name, Station, Distance, Pace).

participants(Count) :- Count = #count{participant(X): participant(X)}.

% Wants to start
:- not station_visit("Ellis", 0).

% Needs to start
:- not station_visit("Nick", 0).

% Accomodate pacing
run_leg("Lauren", leg(8, 8, 9)).
run_leg("Lauren", leg(9, 9, 10)).
run_leg("Lauren", leg(10, 10, 11)).
run_leg("Lauren", leg(11, 11, 12)).
run_leg("Lauren", leg(12, 12, 13)).

% Strollable
:- not stroller_traversible(S1, S2), run_leg("Maya", leg(T,S1,S2)), leg_time(T).
