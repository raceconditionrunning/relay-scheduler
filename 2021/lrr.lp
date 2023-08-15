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
:- not 1{leaderOn(X, T)}1, legTime(T).

% Prefer that leaders don't begin leading on their first exchange
:~ startExchange(X, LeadStartExchange), leaderAssignmentRange(X, legRange(LeadStartExchange, EndExchange)). [ 1@0 , X]

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Generate
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Assign each participant to a range of legs
1{
   assignmentRange(X, legRange(Start, Stop)): legRange(Start, Stop)
}1 :- participant(X).

assignment(X, leg(T, StartExchange, EndExchange)) :- leg(T, StartExchange, EndExchange), StartTime <= T, T <= StopTime, assignmentRange(X, legRange(StartTime, StopTime)).

% If a leader candidate is assigned to a leg, optionally generate a (one contiguous block) leadership assignment from
% within their segment.
0{
    leaderAssignmentRange(X, legRange(StartLead, EndLead)): StartLead=StartExchange..EndExchange, EndLead=StartExchange..EndExchange, StartLead < EndLead
}1 :- willingToLead(X), assignmentRange(X, legRange(StartExchange, EndExchange)).

leaderAssignment(X, leg(T, StartExchange, EndExchange)) :- leg(T, StartExchange, EndExchange), StartTime <= T, T <= StopTime, leaderAssignmentRange(X, legRange(StartTime, StopTime)).

leaderOn(X, T) :- leaderAssignment(X, leg(T, _, _)).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Optimization objectives
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Priority between objectives is lexicographic, largest number to lowest

% Try not to go too far over people's stated limits
#minimize {D @ 4, X: distOverage(X, D), participant(X)}.

% Make people run the distance they want to run
#minimize {D @ 3, X: distDeviation(X, D), participant(X)}.

#minimize {EndDeviation @ 2, X: endDeviation(X, EndDeviation), participant(X)}.

#minimize {Duration @ 1, T: duration(T, Duration), legTime(T)}.

% Provide a key
objective(
    4,"dist overage";
    3,"dist";
    2,"commute";
    1,"duration";
    0,"leader early start"
).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Alternative objectives
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Make people run the pace they want to run
% #minimize {D @ 4: paceDeviation(X, T, D), participant(X), legTime(T)}.
%:- Slack > 1000, paceSlack(X, T, Slack).

% Just get within half a mile for everyone
%:- Deviation > 50, distDiff(X, Deviation).

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
