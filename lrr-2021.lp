% Format: From Angle Lake to Northgate
leg(T - 18, 18 - (T - 18), 18 - (T - 17)) :- T=18..35.

%%% Event constraints

:- leg_count(X, 0), participant(X).
:- C != 2, exchange_count(X, C), participant(X).
:- C < 1, lead_count(T, C), leg_time(T).
% Group safety in downtown
:- C < 3, leg_coverage(T, C), leg(T, X, _), s_name(X, ("Pioneer Square";"International District/Chinatown";"University Street";"Westlake")).


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
    "Yuxuan",       3,  "5.0",  "11.33";
    "James",        4,  "3.0",  "9.0";
    "Jennifer",     16, "3.0",  "10.0";
    "Chandra",      0,  "10.0", "10.0";
    "Ellis",        4,  "10.0", "7.5";
    "Nick",         2,  "9.9",  "8.0";
    "Zach",         13, "6.0",  "10.5";
    "Max",          5,  "3.0",  "9.5";
    "Swati",        2,  "6.2",  "12.0";
    "Sidd",         1,  "5.0",  "11.0";
    "Amal",         1,  "5.0",  "10.0";
    "Maya",         0,  "5.0",  "10.0";
    "Ethan",        4,  "7.0",  "8.5";
    "Sameer",       2,  "3.0",  "9.5";
    "Edward",       2,  "4.0",  "10.0";
    "Ewin",         1,  "7.0",  "9.0";
    %"Jamie",        2,  "10.0", "8.0";
    "Jamie",        2,  "7.0", "8.0";
    "Johanna",      3,  "6.21", "8.0";
    %"Jingwei",      1,  "2.0",  "11.86";
    "Jingwei",      1,  "2.0",  "12.0";
    "Lancelot",     1,  "6.0",  "9.0";
    %"Vishwas",     3,  "2.0",  "20.0";
    "Vishwas",      3,  "1.0",  "20.0";
    %"Reshabh",      2,  "0.5",  "10.0";
    "Reshabh",      2,  "0.5",  "12.0";
    "Brett",        2,  "3.0",  "9.5";
    "Suneja",       11,  "2.0",  "12.84";
    "Pratyush",     2,   "2.0", "10.0";
).

% Designated as responsible for their legs
lead("Yuxuan"; "James"; "Chandra"; "Ellis"; "Zach"; "Nick").

participant(Name)
    :- preference(Name, Station, Distance, Pace).
preferred_pace(Name, Pace)
    :- preference(Name, Station, Distance, Pace).
nearest_station(Name, Station)
    :- preference(Name, Station, Distance, Pace).
preferred_distance(Name, Distance)
    :- preference(Name, Station, Distance, Pace).

participants(Count) :- Count = #count{participant(X): participant(X)}.

% Location exclusions
:- station_visit("Jennifer", 7).

% Strollable
:- not stroller_traversible(S1, S2), run_leg("Maya", leg(T,S1,S2)), leg_time(T).
