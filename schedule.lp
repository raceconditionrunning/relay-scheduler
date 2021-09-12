#program base.

% From Angle Lake to Northgate
leg(T - 18, 18 - (T - 18), 18 - (T - 17)) :- T=18..35.

%leg(T, T, T + 1) :- T=0..17.
%leg(T, 18 - (T - 18), 18 - (T - 17)) :- T=18..35.
leg_time(T) :- leg(T,_,_).

% Exchanges happen before and after each leg.
exchange_time(T1) :- T1 = T + 1, leg_time(T). 
exchange_time(T1) :- T1 = T - 1, leg_time(T). 

%%% Generate

% One person each leg
%1{
%    run_leg(X,leg(A,B,C)): participant(X)
%}1 :- leg(A,B,C).

% Multiple people (potentially) each leg

1{
   run_leg(X, leg(A,B,C)): participant(X) 
}Count :- leg(A,B,C), participants(Count).

% Who runs what index
run(X,T) :- run_leg(X, leg(T,_,_)).

% Summarize assignments
end_station(X, Station) :- s_name(Station, _), leg(T1, _, Station), T1=#max{T:run(X, T), leg_time(T)}, participant(X).
start_station(X, Station) :- s_name(Station, _), leg(T1, Station, _), T1=#min{T:run(X, T), leg_time(T)}, participant(X).
assignment(X,StartName,EndName) :- s_name(StartStation, StartName), s_name(EndStation, EndName), start_station(X, StartStation), end_station(X, EndStation), participant(X).


%%% Plan events

exchange(X, T - 1) :- not run(X, T - 1), run(X, T), participant(X), leg_time(T).
exchange(X, T + 1) :- run(X, T), not run(X, T + 1), participant(X), leg_time(T).

station_visit(X, Station) :- run(X, leg(_, Station, _)).
station_visit(X, Station) :- run(X, leg(_, _, Station)).

%%% Plan metrics

leg_pace(T, M) :- M = #max{P:run(X, T), preferred_pace(X,P), participant(X)}, leg_time(T). 

duration(T, Duration) :- Duration = Distance * M, leg_dist(T,Distance), leg_pace(T, M), leg_time(T).

leg_count(X, C) :- C = #count{run(X, T): run(X, T), participant(X)}, participant(X).

leg_dist(T, D) :- leg(T, S1, S2), distance(S1, S2, D).

leg_climbing(T, Climb) :- leg(T, S1, S2), climbing(S1, S2, Climb).

total_dist(X, Total) :- Total = #sum{Distance: leg_dist(T,Distance), run(X,T), leg_time(T)}, participant(X).

total_climbing(X, Total) :- Total = #sum{Climb: leg_climbing(T,Climb), run(X,T), leg_time(T)}, participant(X).

dist_deviation(X, |G - T|) :- total_dist(X, T), preferred_distance(X, G), participant(X).

end_deviation(X, |Goal - EndStation|) :- nearest_station(X, Goal), end_station(X, EndStation), participant(X).

leg_coverage(T, C) :- C = #count{run(X, T): run(X, T), participant(X)}, leg_time(T).

exchange_count(X, C) :- C = #count{exchange(X,T): exchange(X,T), participant(X), exchange_time(T)}, participant(X).


%%% Reject

:- leg_count(X, 0), participant(X).
:- C != 2, exchange_count(X, C), participant(X).

%%% Optimize

% Priority between objectives is lexicographic, largest number to lowest

% Make people run the distance they want to run
%#minimize {D @ 3: dist_deviation(X, D), participant(X)}.

% Alternatively, just get within half a mile for everyone
:- Deviation > 50, dist_deviation(X, Deviation).

#minimize {Duration @ 2: duration(T, Duration), leg_time(T)}.

#minimize {EndDeviation @ 1: end_deviation(X, EndDeviation), participant(X)}.

#show assignment/3.