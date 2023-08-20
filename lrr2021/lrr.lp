% Format: From Angle Lake to Northgate
leg(T, T, T + 1) :- T=0..17.

% We are only going to assign people to one of these ranges.
legRange(StartTime, StopTime) :- StartTime < StopTime, legTime(StartTime), legTime(StopTime).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Event constraints
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% People are assigned one segment. Although we generate only solutions that obey this, still need this
% constraint for when legs are manually pinned.
:- C != 2, exchangeCount(P, C), participant(P).

% Atleast 2 people on each leg
:- C < 2, legCoverage(T, C), leg(T, _, _).

% Group safety in downtown
:- C < 3, legCoverage(T, C), leg(T, StartTime, _), exchangeName(StartTime, ("Pioneer Square";"International District/Chinatown";"University Street";"Westlake")).

% Exactly one leader assigned per leg
:- not 1{leaderOn(P, T)}1, legTime(T).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Generate
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Assign each participant to a range of legs
1{
   assignmentRange(P, legRange(Start, Stop)): legRange(Start, Stop)
}1 :- participant(P).

assignment(P, leg(T, StartExchange, EndExchange)) :- leg(T, StartExchange, EndExchange), StartTime <= T, T <= StopTime, assignmentRange(P, legRange(StartTime, StopTime)).

% If a leader candidate is assigned to a leg, optionally generate a (one contiguous block) leadership assignment from
% within their segment.
0{
    leaderAssignmentRange(P, legRange(StartLead, EndLead)): StartLead=StartExchange..EndExchange, EndLead=StartExchange..EndExchange, StartLead < EndLead
}1 :- willingToLead(P), assignmentRange(P, legRange(StartExchange, EndExchange)).

leaderAssignment(P, leg(T, StartExchange, EndExchange)) :- leg(T, StartExchange, EndExchange), StartTime <= T, T <= StopTime, leaderAssignmentRange(P, legRange(StartTime, StopTime)).

leaderOn(P, T) :- leaderAssignment(P, leg(T, _, _)).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Optimization
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Prefer that leaders don't begin leading on their first exchange
:~ startExchange(P, LeadStartExchange), leaderAssignmentRange(P, legRange(LeadStartExchange, EndExchange)), objective(Weight, "leader-early-start"). [ 1 @ Weight , P]

% Try to use as many of the willing leaders as we can
:~ not leaderAssignmentRange(P, legRange(_, _)), willingToLead(P), objective(Weight, "leaders-ignored"). [ 1 @ Weight , P]

% Just get within half a mile for everyone
% :~ |Actual - Preferred| > ".50", totalDist(P, Actual), preferredDistance(P, Preferred), participant(P), objective(Weight, "dist-pref-close"). [1 @ Weight, P]

% Lexicographic optimization. Objectives from most to least important. Reorder or remove objectives here
objective(
    4,"dist-pref-overage";
    3,"dist-pref";
    2,"commute-pref";
    1,"duration";
    0,"leader-early-start";
    -1,"leaders-ignored";
    -2,"pace-pref"
).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Preferences
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

preference(
%   Name           End  Dist    Pace
    "Yuxuan",       15,  "5.0",  "11:20";
    "James",        14,  "3.0",  "9:00";
    "Jennifer",     2, "3.0",  "10:00";
    "Chandra",      18,  "10.0", "10:00";
    "Ellis",        4,  "10.0", "7:30";
    "Nick",         16,  "10.0",  "8:00";
    "Zach",         5, "6.0",  "10:30";
    "Max",          13,  "3.0",  "9:30";
    "Swati",        16,  "6.2",  "12:00";
    "Sidd",         17,  "5.0",  "11:00";
    "Amal",         17,  "5.0",  "10:00";
    "Maya",         18,  "5.0",  "10:00";
    "Ethan",        14,  "7.0",  "8:30";
    "Sameer",       16,  "3.0",  "9:30";
    "Edward",       16,  "4.0",  "10:00";
    "Ewin",         17,  "7.0",  "9:00";
    %"Jamie",        16,  "10.0", "8:00";
    "Jamie",        16,  "7.0", "8:00";
    "Johanna",      15,  "6.21", "8:00";
    %"Jingwei",      17,  "2.0",  "11.86";
    "Jingwei",      17,  "2.0",  "12:00";
    "Lancelot",     17,  "6.0",  "9:00";
    %"Vishwas",     15,  "2.0",  "20:00";
    "Vishwas",      15,  "1.0",  "20:00";
    %"Reshabh",      16,  "0.5",  "10:00";
    "Reshabh",      16,  "0.5",  "12:00";
    "Brett",        16,  "3.0",  "9:30";
    "Priyal",       7,  "2.0",  "12:50";
    "Pratyush",     16,   "2.0", "10:00"
).

% Designated as responsible for their legs
willingToLead("Yuxuan";"Chandra"; "Ellis"; "Zach"; "Nick").

participant(Name)
    :- preference(Name, Exchange, Distance, Pace).
preferredPace(Name, Pace)
    :- preference(Name, Exchange, Distance, Pace).
preferredEndExchange(Name, Exchange)
    :- preference(Name, Exchange, Distance, Pace).
preferredDistance(Name, Distance)
    :- preference(Name, Exchange, Distance, Pace).

participants(Count) :- Count = #count{participant(P): participant(P)}.
