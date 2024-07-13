#program base.

% Your instance should define leg/3, distance/3 and participant/1.
% Specify optimization priorities with objective/2.
% Give preferences in preferredPace/2, preferredDistance/2, preferredEndExchange/2, preferredAscent/2, and
% preferredDescent/2 as needed. Some of the helper predicates will only "fire" if you specify relevant
% preferences to keep the ground program as small as possible.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Helper predicates
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Who runs what index
run(P,T) :- assignment(P, leg(T,_,_)).

% Summarize assignments
endExchange(P, Exchange) :- leg(T1, _, Exchange), T1=#max{T:run(P, T), legTime(T)}, participant(P).
startExchange(P, Exchange) :- leg(T1, Exchange, _), T1=#min{T:run(P, T), legTime(T)}, participant(P).

legTime(T) :- leg(T,_,_).

% Exchanges happen before and after each leg.
exchangeTime(T1) :- T1 = T + 1, legTime(T).
exchangeTime(T1) :- T1 = T - 1, legTime(T).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Plan events
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

exchange(P, T - 1) :- not run(P, T - 1), run(P, T), participant(P), legTime(T).
exchange(P, T + 1) :- run(P, T), not run(P, T + 1), participant(P), legTime(T).

exchangeVisit(P, Exchange) :- assignment(P, leg(_, Exchange, _)).
exchangeVisit(P, Exchange) :- assignment(P, leg(_, _, Exchange)).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Plan metrics
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% If no one is assigned, aggregate will emit #inf (infinum, smallest value possible). Restrict with a lower bound
legPace(T, Max) :- Max > 0, Max = #max{Pace:run(P, T), preferredPace(P,Pace), participant(P)}, legTime(T).

legDuration(T, Duration) :- Duration = Distance * M, legDist(T,Distance), legPace(T, M), legTime(T).

legCount(P, C) :- C = #count{T: run(P, T), participant(P)}, participant(P).

legDist(T, D) :- leg(T, S1, S2), distance(S1, S2, D).

legAscent(T, Climb) :- leg(T, S1, S2), ascent(S1, S2, Climb).

legDescent(T, Climb) :- leg(T, S1, S2), descent(S1, S2, Climb).

participantDist(P, Total) :- Total = #sum{Distance: legDist(T,Distance), run(P,T), legTime(T)}, participant(P).

participantAscent(P, Total) :- Total = #sum{Climb: legAscent(T,Climb), run(P,T), legTime(T)}, preferredAscent(P, _), participant(P).

participantDescent(P, Total) :- Total = #sum{Climb: legDescent(T,Climb), run(P,T), legTime(T)}, preferredDescent(P, _) ,participant(P).

legCoverage(T, C) :- C = #count{P: run(P, T), participant(P)}, legTime(T).

% If you need to count exchanges, prefer to do it in an aggregate instead.
% exchangeCount(P, C) :- C = #count{T: exchange(P,T), exchangeTime(T)}, participant(P).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Optimization objectives
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Try not to go too far over people's stated limits
#minimize {@max(Actual - Preferred, 0) @ Priority, P: participantDist(P, Actual), preferredDistance(P, Preferred), participant(P),  objective(Priority, "dist-pref-overage")}.

% Make people run the distance they want to run
#minimize {|Actual - Preferred| @ Priority, P: participantDist(P, Actual), preferredDistance(P, Preferred), participant(P), objective(Priority, "dist-pref")}.

#minimize {EndDeviation @ Priority, P: commuteDistance(Goal, EndExchange, EndDeviation), preferredEndExchange(P, Goal), endExchange(P, EndExchange), participant(P), objective(Priority, "commute-pref")}.

#minimize {Duration @ Priority, T: legDuration(T, Duration), legTime(T), objective(Priority, "duration")}.

% Make people run the pace they want to run
#minimize {|Actual - Preferred| @ Priority, P, T: legPace(T, Actual), run(P, T), preferredPace(P, Preferred), objective(Priority, "pace-pref")}.