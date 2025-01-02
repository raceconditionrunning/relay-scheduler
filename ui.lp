elem(window, window, root).
attr(window, child_layout, flex).
attr(window, flex_direction, column).
%%%%%%%%%%%%%%%%%
elem(menu_bar, menu_bar, window).
attr(menu_bar, title, "Relay Scheduling").
attr(menu_bar, icon, "fa-running").

elem(menu_bar_next, button, menu_bar).
attr(menu_bar_next, label, "Next").
attr(menu_bar_next, icon, "fa-forward-step").
when(menu_bar_next, click, call, next_solution(opt)).

elem(cost_summary, container, window).
attr(cost_summary, order, 1).
attr(cost_summary, child_layout, flex).
attr(cost_summary, flex_direction, row).
elem(cost_summary(Index), container, cost_summary) :- _clinguin_cost(Index, Cost).
attr(cost_summary(Index), order, Index) :- _clinguin_cost(Index, Cost).
elem(cost_summary_label(Index), label, cost_summary(Index)) :- _clinguin_cost(Index, Cost).

attr(cost_summary_label(Index), label, @concat(CostName, ": ", Cost)) :- _clinguin_cost(Index, Cost), objective(Index, CostName).
%%%%%%%%%
elem(workarea, container, window).
attr(workarea, child_layout, flex).
attr(workarea, flex_direction, row).
attr(workarea, order, 2).
elem(participants, container, workarea).

elem(participant(P), container, participants):- participant(P).
attr(participant(P), order, P):- participant(P).
attr(participant(P), width, 200):- participant(P).
attr(participant(P), class, ("bg-primary";"bg-opacity-25";"rounded";
                       "d-flex";"flex-column";"align-items-start";
                       "p-2";"m-2"
                     )):- participant(P).

elem(participant_label(P), label, participant(P)):- participant(P).
attr(participant_label(P), order, 1):- participant(P).
attr(participant_label(P), label, @concat("","",P)):- participant(P).

elem(leg_dd((P,C)), dropdown_menu, participant(P)):- participant(P), C=1..2.
attr(leg_dd((P,C)), order, C+1):- participant(P), C=1..2.
attr(leg_dd((P,C)), class, ("btn-sm";"btn-primary";"m-2")):- participant(P), C=1..2.
attr(leg_dd((P,1)), selected, N):- _clinguin_assume(startExchange(P, StartExchange),true), exchangeName(StartExchange, N).
% Classes applied to the button, not the container around the menu items.
attr(leg_dd((P,1)), class, ("d-flex";"flex-column")):- participant(P).

elem(leg_ddi((P,1), StartExchange), dropdown_menu_item, leg_dd((P,1))):- leg(Start, StartExchange, _), participant(P).
% Order doesn't apply because menu isn't displayed "flex"
attr(leg_ddi((P,1), StartExchange), order, Start):- leg(Start, StartExchange, _), participant(P).

attr(leg_ddi((P,1),StartExchange), label, N):- leg(Start, StartExchange, _), participant(P), exchangeName(StartExchange, N).
when(leg_ddi((P,1),StartExchange), click, call, add_assumption(startExchange(P, StartExchange),true)):-
                     participant(P), leg(Start, StartExchange, _).


elem(leg_ddi((P,C),remove), dropdown_menu_item, leg_dd((P,C))):- participant(P), C=1..2.
attr(leg_ddi((P,C),remove), label, "-"):- participant(P), C=1..2.
when(leg_ddi((P,1),remove), click, call, remove_assumption_signature(startExchange(P, any))):- participant(P).


%%------------------------------
%% Assignments
%% -----------------------------
elem(legs, container, workarea).

elem(leg(T, StartExchange, EndExchange), container, legs):- leg(T, StartExchange, EndExchange).
attr(leg(T, StartExchange, EndExchange), order, T):- leg(T, StartExchange, EndExchange).
attr(leg(T, StartExchange, EndExchange), width, 600):- leg(T, StartExchange, EndExchange).
attr(leg(T, StartExchange, EndExchange), class, ("bg-primary";"bg-opacity-25";"rounded";
                       "d-flex";"flex-column";"align-items-start";
                       "p-2";"m-2"
                     )):- leg(T, StartExchange, EndExchange).

 elem(leg_label(T, StartExchange, EndExchange), label, leg(T, StartExchange, EndExchange)):- leg(T, StartExchange, EndExchange).
 attr(leg_label(T, StartExchange, EndExchange), label, @concat(StartName," -> ",EndName)):- exchangeName(StartExchange, StartName), exchangeName(EndExchange, EndName), leg(T, StartExchange, EndExchange).

elem(assignment_label(P, leg(T, StartExchange, EndExchange)), label, leg(T, StartExchange, EndExchange)):- assignment(P, leg(T, StartExchange, EndExchange)).
attr(assignment_label(P, leg(T, StartExchange, EndExchange)), order, P):- assignment(P, leg(T, StartExchange, EndExchange)).
attr(assignment_label(P, leg(T, StartExchange, EndExchange)), label, @concat("",P)):- assignment(P, leg(T, StartExchange, EndExchange)).
