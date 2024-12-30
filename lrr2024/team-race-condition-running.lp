#program race_condition_running.
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

% Preferences are given in TSV


% We are only going to assign people to one of these ranges.
legRange(StartTime, StopTime) :- StartTime < StopTime, legTime(StartTime), legTime(StopTime).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Event constraints
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% People are assigned one segment. Although we generate only solutions that obey this, still need this
% constraint for when legs are manually pinned.
:- C != 2, exchangeCount(P, C), participant(P).

% Atleast 2 people on each leg
%:- C < 2, legCoverage(T, C), leg(T, _, _).

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
:~ startExchange(P, LeadStartExchange), leg(T, LeadStartExchange, _), leaderAssignmentRange(P, legRange(LeadStartT, _)), objective(Priority, "leader-early-start"). [ 1 @ Priority , P]

% Try to use as many of the willing leaders as we can
:~ not leaderAssignmentRange(P, legRange(_, _)), willingToLead(P), objective(Priority, "leaders-ignored"). [ 1 @ Priority , P]


% Just get within half a mile for everyone
% :~ |Actual - Preferred| > ".50", totalDist(P, Actual), preferredDistance(P, Preferred), participant(P), objective(Priority, "dist-pref-close"). [1 @ Priority, P]


participants(Count) :- Count = #count{participant(X): participant(X)}.
