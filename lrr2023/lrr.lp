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
% Optimization
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Prefer that leaders don't begin leading on their first exchange
:~ startExchange(P, LeadStartExchange), leaderAssignmentRange(P, legRange(LeadStartExchange, EndExchange)), objective(Weight, "leader-early-start"). [ 1 @ Weight , P]

% Try to use as many of the willing leaders as we can
:~ not leaderAssignmentRange(P, legRange(_, _)), willingToLead(P), objective(Weight, "leaders-ignored"). [ 1 @ Weight , P]

% Just get within half a mile for everyone
% :~ |Actual - Preferred| > ".50", totalDist(P, Actual), preferredDistance(P, Preferred), participant(P), objective(Weight, "dist-pref-close"). [1 @ Weight, P]


participant(Name)
    :- preference(Name, Exchange, Distance, Pace, _).
preferredPace(Name, Pace)
    :- preference(Name, Exchange, Distance, Pace, _).
preferredEndExchange(Name, Exchange)
    :- preference(Name, Exchange, Distance, Pace, _), Exchange >= 0.
preferredDistance(Name, Distance)
    :- preference(Name, Exchange, Distance, Pace, _).
willingToLead(Name) :- preference(Name, _, _, _, Leader), Leader == 1.

participants(Count) :- Count = #count{participant(X): participant(X)}.
