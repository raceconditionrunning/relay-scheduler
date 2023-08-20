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
% Optimization objectives
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Priority between objectives is lexicographic, largest number to lowest

% Try not to go too far over people's stated limits
#minimize {@max(Actual - Preferred, 0) @ 4, P: totalDist(P, Actual), preferredDistance(P, Preferred), participant(P)}.

% Make people run the distance they want to run
#minimize {|Actual - Preferred| @ 3, P: totalDist(P, Actual), preferredDistance(P, Preferred), participant(P)}.

#minimize {EndDeviation @ 2, P: endDeviation(P, EndDeviation), participant(P)}.

#minimize {Duration @ 1, T: duration(T, Duration), legTime(T)}.

% Prefer that leaders don't begin leading on their first exchange
:~ startExchange(P, LeadStartExchange), leaderAssignmentRange(X, legRange(LeadStartExchange, EndExchange)). [ 1@0 , P]

% Try to use as many of the willing leaders as we can
:~ not leaderAssignmentRange(P, legRange(_, _)), willingToLead(P). [ 1@-1 , P]

% Provide a key
objective(
    4,"dist overage";
    3,"dist";
    2,"commute";
    1,"duration";
    0,"leader early start";
    -1,"leaders ignored"
).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Alternative objectives
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Make people run the pace they want to run
% #minimize {|Actual - Preferred| @ 4: legPace(T, Actual), run(P, T), preferredPace(P, Preferred)}.

% Just get within half a mile for everyone
%:- |Actual - Preferred| > ".50", totalDist(P, Actual), preferredDistance(P, Preferred), participant(P).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Preferences
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

preference(
%   Name           End  Dist    Pace
    "James",        14,  "8.0",  "9:30";
    "Nick",         14,  "13.0",  "9:00";
    "Lauren",       17,  "4.0",  "16:00";
    %"Lauren",       17,  "6.0",  "12:45";
    "Yuxuan",       17,  "8.0",  "12:00";
    "Maya",         17,  "3.0",  "10:00";
    "Chandra",      7,  "6.0", "10:00";
    "Dhruba",       14,  "8.0", "8:30";
    "Zach E.",      15,  "4.0", "8:30";
    "Justin",       15,  "6.0", "8:00";
    "Brett",        16,  "6.0",  "11:00";
    "Ethan",        14,  "6.0",  "9:30";
    "Zach T.",      6,   "4.0",  "11:00";
    "Ryan",         15,  "1.0",  "9:00";
    "Kevin",        13,  "3.0",  "12:00";
    "Edward",       18,  "4.0",  "10:00";
    "Marius",       16,  "6.0",  "9:00";
    "Ewin",         18,  "8.0",  "9:00";
    "Ellis",        14,  "13.0", "9:00"
).

% Designated as responsible for their legs
willingToLead("Yuxuan"; "James"; "Chandra"; "Ellis"; "Zach"; "Nick"; "Edward").

participant(Name)
    :- preference(Name, Exchange, Distance, Pace).
preferredPace(Name, Pace)
    :- preference(Name, Exchange, Distance, Pace).
preferredEndExchange(Name, Exchange)
    :- preference(Name, Exchange, Distance, Pace).
preferredDistance(Name, Distance)
    :- preference(Name, Exchange, Distance, Pace).

participants(Count) :- Count = #count{participant(P): participant(P)}.
