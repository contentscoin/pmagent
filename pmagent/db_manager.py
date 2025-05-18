import sqlite3
import os
import json
from datetime import datetime
from typing import Optional

# --- DB 파일 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PROJECT_MASTER_DB_PATH = os.path.join(DATA_DIR, 'project_master.sqlite')
AGENT_SHARED_DB_PATH = os.path.join(DATA_DIR, 'agent_shared.sqlite')

# 데이터 디렉토리 생성 (스크립트 로드 시점에 실행되어도 무방)
os.makedirs(DATA_DIR, exist_ok=True)

# --- DB 연결 함수 ---
def get_db_connection(db_path, timeout=10.0):
    """SQLite DB에 연결하고 커서를 반환합니다."""
    conn = sqlite3.connect(db_path, timeout=timeout)
    conn.row_factory = sqlite3.Row # 결과를 딕셔너리 형태로 접근 가능하도록 설정
    return conn

# --- ProjectMasterDB 초기화 및 테이블 생성 ---
def init_project_master_db():
    print("[DEBUG] init_project_master_db() CALLED") # DEBUG PRINT
    """ProjectMasterDB를 초기화하고 필요한 테이블을 생성합니다."""
    conn = get_db_connection(PROJECT_MASTER_DB_PATH)
    cursor = conn.cursor()

    # projects 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        project_name TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, active, completed, archived
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # master_tasks 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS master_tasks (
        task_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending', -- pending, assigned, in_progress, completed, failed, reported
        assigned_to_agent_type TEXT, -- e.g., 'BackendAgent', 'DesignerAgent'
        dependencies TEXT, -- JSON string of task_ids
        results_summary TEXT, -- JSON string or simple text summary of results
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (project_id)
    )
    ''')
    
    # updated_at 트리거 설정 (projects)
    # 이 트리거는 SQLite 3.38.0+ 에서 지원하는 문법을 포함할 수 있어,
    # 보다 안전하게는 애플리케이션 레벨에서 updated_at을 관리하거나,
    # 호환성 높은 기본 트리거 문법을 사용합니다.
    # 여기서는 단순성을 위해, 애플리케이션 코드에서 updated_at을 직접 설정하는 것을 권장하며,
    # 트리거는 예시로 남겨두되, 실제 운영 시 테스트가 필요합니다.
    try:
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_projects_updated_at_trigger
        AFTER UPDATE ON projects
        FOR EACH ROW
        WHEN OLD.updated_at = NEW.updated_at OR OLD.updated_at IS NULL OR NEW.updated_at IS NULL -- 루프 방지 및 명시적 업데이트 시에만 동작
        BEGIN
            UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE project_id = OLD.project_id;
        END;
        ''')
    except sqlite3.OperationalError as e:
        print(f"Warning: Could not create trigger for projects table (might be an older SQLite version or syntax issue): {e}")


    try:
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_master_tasks_updated_at_trigger
        AFTER UPDATE ON master_tasks
        FOR EACH ROW
        WHEN OLD.updated_at = NEW.updated_at OR OLD.updated_at IS NULL OR NEW.updated_at IS NULL
        BEGIN
            UPDATE master_tasks SET updated_at = CURRENT_TIMESTAMP WHERE task_id = OLD.task_id;
        END;
        ''')
    except sqlite3.OperationalError as e:
        print(f"Warning: Could not create trigger for master_tasks table: {e}")


    conn.commit()
    conn.close()

# --- AgentSharedDB 초기화 및 테이블 생성 ---
def init_agent_shared_db():
    print("[DEBUG] init_agent_shared_db() CALLED") # DEBUG PRINT
    """AgentSharedDB를 초기화하고 필요한 테이블을 생성합니다."""
    conn = get_db_connection(AGENT_SHARED_DB_PATH)
    cursor = conn.cursor()

    # agent_reports 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL, -- e.g., "DesignerAgent_instance1"
        task_id TEXT, -- Related master_task_id, can be NULL if not task-specific report
        report_type TEXT NOT NULL, -- 'progress_update', 'result_submission', 'error_report', 'inter_agent_request', 'general_log'
        content TEXT, -- JSON string for flexible data
        is_processed_by_pm INTEGER DEFAULT 0, -- 0 for false, 1 for true
        processed_at TEXT, -- Timestamp when processed by PM
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# --- CRUD 함수 예시 (추후 확장 예정) ---

# ProjectMasterDB - Projects
def add_project(project_id, project_name, status='pending'):
    conn = get_db_connection(PROJECT_MASTER_DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO projects (project_id, project_name, status, created_at, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (project_id, project_name, status))
        conn.commit()
        return project_id
    except sqlite3.IntegrityError:
        print(f"Error: Project with ID {project_id} already exists.")
        return None
    finally:
        conn.close()

def get_project(project_id):
    conn = get_db_connection(PROJECT_MASTER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    return dict(project) if project else None

# ProjectMasterDB - MasterTasks
def add_master_task(task_id, project_id, title, description=None, status='pending', assigned_to_agent_type=None, dependencies=None):
    conn = get_db_connection(PROJECT_MASTER_DB_PATH)
    cursor = conn.cursor()
    dependencies_json = json.dumps(dependencies) if dependencies else None
    try:
        cursor.execute('''
        INSERT INTO master_tasks (task_id, project_id, title, description, status, assigned_to_agent_type, dependencies, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (task_id, project_id, title, description, status, assigned_to_agent_type, dependencies_json))
        conn.commit()
        return task_id
    except sqlite3.IntegrityError:
        print(f"Error: Task with ID {task_id} already exists.")
        return None
    finally:
        conn.close()

def get_master_task(task_id):
    conn = get_db_connection(PROJECT_MASTER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM master_tasks WHERE task_id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    if task:
        task_dict = dict(task)
        if task_dict.get('dependencies'):
            task_dict['dependencies'] = json.loads(task_dict['dependencies'])
        return task_dict
    return None

def update_master_task_status(task_id, status, results_summary=None):
    conn = get_db_connection(PROJECT_MASTER_DB_PATH)
    cursor = conn.cursor()
    current_time = datetime.now().isoformat()
    results_summary_json = json.dumps(results_summary) if results_summary is not None else None

    if results_summary_json is not None:
        cursor.execute('''
        UPDATE master_tasks SET status = ?, results_summary = ?, updated_at = ?
        WHERE task_id = ?
        ''', (status, results_summary_json, current_time, task_id))
    else:
        cursor.execute('''
        UPDATE master_tasks SET status = ?, updated_at = ?
        WHERE task_id = ?
        ''', (status, current_time, task_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_pending_assignable_task_for_agent(agent_type: str, project_id: Optional[str] = None):
    """지정된 에이전트 유형에 할당 가능하고 아직 완료되지 않은 가장 오래된 태스크를 가져옵니다."""
    conn = get_db_connection(PROJECT_MASTER_DB_PATH)
    cursor = conn.cursor()
    query = """
    SELECT * FROM master_tasks
    WHERE (status = 'pending' OR status = 'assigned') 
    AND assigned_to_agent_type = ?
    """
    params = [agent_type]

    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    
    query += " ORDER BY created_at ASC LIMIT 1"

    cursor.execute(query, tuple(params))
    task = cursor.fetchone()
    conn.close()

    if task:
        task_dict = dict(task)
        if task_dict.get('dependencies'):
            try:
                task_dict['dependencies'] = json.loads(task_dict['dependencies'])
            except json.JSONDecodeError:
                print(f"Warning: Could not decode dependencies JSON for task {task_dict.get('task_id')}: {task_dict.get('dependencies')}")
                task_dict['dependencies'] = [] # 또는 None, 또는 원본 문자열 유지
        return task_dict
    return None

# AgentSharedDB - AgentReports
def add_agent_report(agent_id, report_type, content, task_id=None):
    conn = get_db_connection(AGENT_SHARED_DB_PATH)
    cursor = conn.cursor()
    content_json = json.dumps(content)
    try:
        cursor.execute('''
        INSERT INTO agent_reports (agent_id, task_id, report_type, content, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (agent_id, task_id, report_type, content_json))
        conn.commit()
        report_id = cursor.lastrowid
        return report_id
    except Exception as e:
        print(f"Error adding agent report: {e}")
        return None
    finally:
        conn.close()

def get_unprocessed_agent_reports(limit=100):
    conn = get_db_connection(AGENT_SHARED_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM agent_reports 
    WHERE is_processed_by_pm = 0 
    ORDER BY created_at ASC
    LIMIT ?
    ''', (limit,))
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    for report in reports:
        if report.get('content'):
            try:
                report['content'] = json.loads(report['content'])
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON content for report_id {report.get('report_id')}")
                # 내용을 그대로 두거나, 오류 처리를 할 수 있습니다.
    return reports

def mark_agent_report_as_processed(report_id):
    conn = get_db_connection(AGENT_SHARED_DB_PATH)
    cursor = conn.cursor()
    processed_time = datetime.now().isoformat()
    try:
        cursor.execute('''
        UPDATE agent_reports SET is_processed_by_pm = 1, processed_at = ?
        WHERE report_id = ?
        ''', (processed_time, report_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error marking agent report as processed: {e}")
        return False
    finally:
        conn.close()

def check_db_connection():
    """
    데이터베이스 연결을 확인합니다.
    Project Master DB와 Agent Shared DB 모두에 연결을 시도합니다.
    """
    db_paths_to_check = {
        "Project Master DB": PROJECT_MASTER_DB_PATH,
        "Agent Shared DB": AGENT_SHARED_DB_PATH
    }
    all_connections_ok = True

    for db_name, db_path in db_paths_to_check.items():
        try:
            # 데이터베이스 파일 존재 여부 먼저 확인
            if not os.path.exists(db_path):
                print(f"Database check: {db_name} file does not exist at {db_path}. Assuming new DB, will be created on init.")
                # 파일이 없으면 연결 시도 시 자동으로 생성되므로, 여기서는 경고만 하고 넘어갈 수 있습니다.
                # 또는 엄격하게 False를 반환할 수도 있습니다. 현재는 초기화 시 생성될 것을 가정합니다.
                # all_connections_ok = False # 엄격하게 하려면 주석 해제
                # break # 엄격하게 하려면 주석 해제
                continue # 다음 DB 체크로 넘어감

            conn = get_db_connection(db_path)
            # 간단한 쿼리로 연결 활성 상태 확인 (선택 사항, connect 자체로도 확인 가능)
            # cursor = conn.cursor()
            # cursor.execute("SELECT 1")
            conn.close()
            print(f"Database check: Successfully connected to {db_name} at {db_path}.")
        except sqlite3.Error as e:
            print(f"Database check: Failed to connect to {db_name} at {db_path}. Error: {e}")
            all_connections_ok = False
            break # 하나의 DB라도 연결 실패하면 중단
        except Exception as e:
            print(f"Database check: An unexpected error occurred while checking {db_name} at {db_path}. Error: {e}")
            all_connections_ok = False
            break

    if all_connections_ok:
        print("Database connection check: All specified databases are accessible.")
    else:
        print("Database connection check: One or more database connections failed.")
    return all_connections_ok

if __name__ == '__main__':
    print(f"Data directory: {DATA_DIR}")
    print(f"Project Master DB path: {PROJECT_MASTER_DB_PATH}")
    print(f"Agent Shared DB path: {AGENT_SHARED_DB_PATH}")
    
    # init_project_master_db()와 init_agent_shared_db()는 mcp_server.py에서 명시적으로 호출합니다.
    print("To initialize, run from mcp_server.py or uncomment lines below for direct test.")

    # 테스트 코드 예시 (직접 실행 시 아래 주석 해제)
    # print("Running test scenario...")
    # if not (os.path.exists(PROJECT_MASTER_DB_PATH) and os.path.exists(AGENT_SHARED_DB_PATH)):
    #     print("Initializing DBs for testing...")
    #     init_project_master_db()
    #     init_agent_shared_db()
    #     print("DBs initialized.")
    # else:
    #     # 테스트를 위해 기존 DB 파일 삭제 후 재생성 (주의! 실제 데이터 손실 가능)
    #     # print("Re-initializing DBs for clean test...")
    #     # if os.path.exists(PROJECT_MASTER_DB_PATH): os.remove(PROJECT_MASTER_DB_PATH)
    #     # if os.path.exists(AGENT_SHARED_DB_PATH): os.remove(AGENT_SHARED_DB_PATH)
    #     # init_project_master_db()
    #     # init_agent_shared_db()
    #     # print("DBs re-initialized.")
    #     pass # 이미 존재하면 그대로 사용

    # print("\n--- Project & Task Test ---")
    # project_id = add_project("proj_main_001", "Main Test Project")
    # if project_id:
    #     print(f"Added project: {get_project(project_id)}")
    #     task_id_1 = add_master_task("task_m_001", project_id, "Design UI Mockups", dependencies=None, assigned_to_agent_type="DesignerAgent")
    #     task_id_2 = add_master_task("task_m_002", project_id, "Develop API Endpoints", dependencies=["task_m_001"], assigned_to_agent_type="BackendAgent")
    #     if task_id_1:
    #         print(f"Added task 1: {get_master_task(task_id_1)}")
    #         update_master_task_status(task_id_1, "assigned")
    #         print(f"Updated task 1: {get_master_task(task_id_1)}")
    #     if task_id_2:
    #         print(f"Added task 2: {get_master_task(task_id_2)}")

    # print("\n--- Agent Report Test ---")
    # if task_id_1:
    #     report_id_1 = add_agent_report("DesignerAgent_Inst_A", "progress_update", {"status": "Sketching phase complete", "progress": 50}, task_id=task_id_1)
    #     if report_id_1:
    #         print(f"Added agent report (ID: {report_id_1}) for task {task_id_1}")
        
    #     report_id_2 = add_agent_report("DesignerAgent_Inst_A", "result_submission", {"design_file": "/path/to/mockup_v1.png", "notes": "Initial version"}, task_id=task_id_1)
    #     if report_id_2:
    #         print(f"Added agent report (ID: {report_id_2}) for task {task_id_1}")

    # unprocessed_reports = get_unprocessed_agent_reports()
    # print(f"\nUnprocessed reports ({len(unprocessed_reports)}):")
    # for report in unprocessed_reports:
    #     print(f"  Report ID: {report['report_id']}, Agent: {report['agent_id']}, Type: {report['report_type']}, Content: {report['content']}")
    #     # 테스트 시에는 여기서 바로 처리된 것으로 마크하지 않습니다.
    #     # mark_agent_report_as_processed(report['report_id'])
    #     # print(f"    Marked report {report['report_id']} as processed.")

    # # PM이 task_id_1에 대한 DesignerAgent_Inst_A의 result_submission 보고를 처리했다고 가정
    # if task_id_1 and unprocessed_reports: # 실제로는 특정 report_id를 찾아야 함
    #     # 예시로 첫번째 리포트를 처리한다고 가정 (실제로는 내용 확인 후 task_id_1에 해당하는 report를 찾아야함)
    #     example_report_to_process = next((r for r in unprocessed_reports if r['task_id'] == task_id_1 and r['report_type'] == 'result_submission'), None)
    #     if example_report_to_process:
    #         print(f"\nSimulating PM processing report {example_report_to_process['report_id']} for task {task_id_1}")
    #         update_master_task_status(task_id_1, "reported", results_summary=example_report_to_process['content'])
    #         mark_agent_report_as_processed(example_report_to_process['report_id'])
    #         print(f"Updated master task {task_id_1}: {get_master_task(task_id_1)}")
    #         print(f"Marked report {example_report_to_process['report_id']} as processed.")

    # print("\nTest scenario finished.")

    if check_db_connection():
        print("Database connection is OK.")
    else:
        print("Failed to connect to the database.") 