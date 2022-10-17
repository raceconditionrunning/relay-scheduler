#program base.

% Your instance should define leg/3, distance/3, climbing/3, as well
% Give preferences in preferred_pace/2 and preferred_distance/2 if needed.

%%% Helper predicates

% Who runs what index
run(X,T) :- run_leg(X, leg(T,_,_)).

% Summarize assignments
end_station(X, Station) :- s_name(Station, _), leg(T1, _, Station), T1=#max{T:run(X, T), leg_time(T)}, participant(X).
start_station(X, Station) :- s_name(Station, _), leg(T1, Station, _), T1=#min{T:run(X, T), leg_time(T)}, participant(X).
assignment(X,StartName,EndName) :- s_name(StartStation, StartName), s_name(EndStation, EndName), start_station(X, StartStation), end_station(X, EndStation), participant(X).

leg_time(T) :- leg(T,_,_).

% Exchanges happen before and after each leg.
exchange_time(T1) :- T1 = T + 1, leg_time(T).
exchange_time(T1) :- T1 = T - 1, leg_time(T).

%%% Plan events

exchange(X, T - 1) :- not run(X, T - 1), run(X, T), participant(X), leg_time(T).
exchange(X, T + 1) :- run(X, T), not run(X, T + 1), participant(X), leg_time(T).

station_visit(X, Station) :- run_leg(X, leg(_, Station, _)).
station_visit(X, Station) :- run_leg(X, leg(_, _, Station)).

%%% Plan metrics

leg_pace(T, M) :- M = #max{P:run(X, T), preferred_pace(X,P), participant(X)}, leg_time(T). 

duration(T, Duration) :- Duration = Distance * M, leg_dist(T,Distance), leg_pace(T, M), leg_time(T).

leg_count(X, C) :- C = #count{run(X, T): run(X, T), participant(X)}, participant(X).

lead_count(T, C) :- C = #count{run(X, T): run(X, T), participant(X), lead(X)}, leg_time(T).

leg_dist(T, D) :- leg(T, S1, S2), distance(S1, S2, D).

leg_ascent(T, Climb) :- leg(T, S1, S2), ascent(S1, S2, Climb).

total_dist(X, Total) :- Total = #sum{Distance: leg_dist(T,Distance), run(X,T), leg_time(T)}, participant(X).

total_ascent(X, Total) :- Total = #sum{Climb: leg_ascent(T,Climb), run(X,T), leg_time(T)}, participant(X).

dist_diff(X, Actual - Preferred) :- total_dist(X, Actual), preferred_distance(X, Preferred), participant(X).
dist_deviation(X, |Diff|) :- dist_diff(X, Diff).
dist_overage(X, Overage) :- Overage = #max{Deviation: dist_diff(X, Deviation); 0}, participant(X).

end_deviation(X, |Goal - EndStation|) :- nearest_station(X, Goal), end_station(X, EndStation), participant(X).

leg_coverage(T, C) :- C = #count{run(X, T): run(X, T), participant(X)}, leg_time(T).

exchange_count(X, C) :- C = #count{exchange(X,T): exchange(X,T), participant(X), exchange_time(T)}, participant(X).

pace_deviation(X, T, Actual - Preferred) :- leg_pace(T, Actual), run(X, T), preferred_pace(X, Preferred).
% How much faster _could_ this person run
pace_slack(X, T, Slack) :- Slack = #max{Deviation;0}, pace_deviation(X, T, Deviation).
