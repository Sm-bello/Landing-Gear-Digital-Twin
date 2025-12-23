% =========================================================================
%   ✈️  AEROTWIN MASTER CONSOLE (TURBO EDITION - V5.1) ✈️
%   Features: Auto-Fix on Start | Persistent Connection | Fast Restart
% =========================================================================

% 1. FORCE LOAD DATABASE DRIVER
try
    javaaddpath('C:\Users\User\Desktop\High_Fidelity_LandingGear\Drivers\postgresql-42.7.3.jar');
catch
end

% 2. SETUP & AUTO-FIX (Runs immediately before Menu)
dbclear all; 
warning('off','all'); 
clc; 

fprintf('🔧 INITIALIZING SYSTEM & FIXING SIMULINK ERRORS...\n');

% --- A. Define Model ---
modelName = 'Fancy_Landing_Gear'; 

% --- B. Ensure Model is Loaded ---
if ~bdIsLoaded(modelName)
    load_system(modelName);
end

% --- C. Inject Variables to Fix Red Blocks ---
assignin('base', 'k_strut_current', 150000); 
assignin('base', 'b_strut_current', 4000);
assignin('base', 'step_initial', 0);
assignin('base', 'step_final', 1);      
assignin('base', 'step_time_var', 1);

% --- D. Force Update to Clear Errors ---
try
    set_param(modelName, 'SimulationCommand', 'update');
    fprintf('✅ Model Updated: Variables injected successfully.\n');
catch
    fprintf('⚠️ Model Update Skipped (Model might be compiling or running).\n');
end

% 3. MAIN MENU
fprintf('\n   AEROTWIN DIGITAL TWIN SYSTEM (TURBO) \n');
fprintf('   1. 📊 Batch Analysis\n');
fprintf('   2. 🎬 Hollywood Replay\n');
fprintf('   3. 📡 Live Monitor (Real-Time Sync)\n');
fprintf('   4. ❌ Exit\n');

choice = input('Select a Mode (1-4): ');

switch choice
    case 3, run_live_monitor(modelName); % Pass modelName to function
    case 4, fprintf('Goodbye! ✈️\n');
    otherwise, fprintf('Mode not implemented in this snippet.\n');
end

% =========================================================================
%   MODE 3: LIVE MONITOR (OPTIMIZED FOR SPEED)
% =========================================================================
function run_live_monitor(modelName)
    fprintf('\n📡 STARTING LIVE MONITOR... (High-Speed Sync)\n');
    
    % --- 🚀 PERFORMANCE TWEAK: FAST RESTART ---
    set_param(modelName, 'FastRestart', 'on'); 
    set_param(modelName, 'SimulationMode', 'normal'); 
    
    % --- 🚀 PERFORMANCE TWEAK: PERSISTENT CONNECTION ---
    conn = get_db_connection();
    
    if ~isopen(conn)
        fprintf('❌ Connection Failed. Check Database.\n');
        return;
    end
    
    % Get initial timestamp
    try
        curr = fetch(conn, 'SELECT MAX(arrival_time) as max_time FROM flight_operations');
        last_time = curr.max_time{1}; 
        if isempty(last_time), last_time = '1900-01-01 00:00:00'; end
    catch
        last_time = '1900-01-01 00:00:00'; 
    end
    
    fprintf('✅ Connected & Ready. Waiting for signals...\n');
    
    while true
        try
            % 1. Check Connection (Reconnect if dropped)
            if ~isopen(conn)
                fprintf('⚠️ Connection lost. Reconnecting...\n');
                conn = get_db_connection();
            end
            
            % 2. Fast Query
            query = sprintf('SELECT * FROM flight_operations WHERE arrival_time > ''%s'' ORDER BY arrival_time ASC LIMIT 1', last_time);
            new_row = fetch(conn, query);
            
            if ~isempty(new_row)
                % Update Timestamp immediately
                last_time = strbullet(new_row.arrival_time); 
                
                raw_phase = new_row.phase;
                if iscell(raw_phase), phase = raw_phase{1}; else, phase = raw_phase; end
                
                % --- TRIGGER LOGIC ---
                if contains(phase, 'Takeoff')
                    fprintf('[%s] 🛫 TAKEOFF -> Retracting\n', last_time);
                    assignin('base', 'step_initial', 1); 
                    assignin('base', 'step_final', 0);
                    
                    % Update Params before Sim
                    set_param(modelName, 'SimulationCommand', 'update');
                    sim(modelName, 'StopTime', '5'); 
                    
                elseif contains(phase, 'Approach')
                    fprintf('[%s] 🛬 APPROACH -> Extending\n', last_time);
                    assignin('base', 'step_initial', 0); 
                    assignin('base', 'step_final', 1);
                    
                    % Update Params before Sim
                    set_param(modelName, 'SimulationCommand', 'update');
                    sim(modelName, 'StopTime', '5'); 
                    
                elseif contains(phase, 'Landing')
                    health = new_row.main_strut_health;
                    fprintf('[%s] 💥 IMPACT (Health: %.1f%%)\n', last_time, health);
                    
                    [k, b] = calculate_physics(new_row);
                    assignin('base', 'k_strut_current', k);
                    assignin('base', 'b_strut_current', b);
                    assignin('base', 'step_initial', 1); 
                    assignin('base', 'step_final', 1);
                    
                    % Update Params before Sim
                    set_param(modelName, 'SimulationCommand', 'update');
                    sim(modelName, 'StopTime', '5'); 
                end
            else
                % 🚀 TURBO PAUSE: Only wait 0.05s (50ms)
                pause(0.05); 
            end
            
        catch ME 
            fprintf('⚠️ Error: %s\n', ME.message); 
            pause(1);
        end
    end
end

function [k, b] = calculate_physics(flightData)
    h = double(max(0, flightData.main_strut_health));
    k = 1.5e5 * (0.3 + 0.7*(h/100)); 
    b = 4000  * (0.3 + 0.7*(h/100));
end

function str = strbullet(val)
    if iscell(val), str = val{1}; else, str = char(val); end
end

function conn = get_db_connection()
    conn = database('project_db', 'postgres', 'A#1Salamatu', 'org.postgresql.Driver', 'jdbc:postgresql://localhost:5432/project_db');
end
