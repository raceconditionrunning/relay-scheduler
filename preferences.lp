preference(
%   Name           End  Dist    Pace
    "Yuxuan",       3,  "5.0",  "11.33";
    "James",        4,  "6.0",  "9.0";
    "Jennifer",     16, "3.0",  "10.0";
    "Chandra",      0,  "10.0", "10.0";
    "Ellis",        4,  "10.0", "7.5";
    "Nick",         2,  "8.0",  "9.0";
    "Zach",         13, "6.0",  "10.5";
    "Max",          5,  "3.0",  "9.5";
    "Swati",        2,  "6.2",  "12.0";
    "Sidd",         5,  "5.0",  "11.0";
).

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

% Avoid serious climbs
:- Climb > 400,  total_climbing("Jennifer", Climb).
:- Climb > 400,  total_climbing("Swati", Climb).