"""Folder Creator 도구의 연산 Pipeline"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from tools.common.log_utils import get_tool_logger
from tools.folder_creator.functions import create_folders


class FolderCreatorWorker(QObject):
    """폴더 생성 작업을 처리하는 Worker (Pipeline)"""
    progressed = Signal(str)
    progress = Signal(int, int)  # current, total
    finished = Signal(int)  # created_count
    failed = Signal(str)

    def __init__(
        self,
        parent_path: Path,
        count: int,
        prefix: str,
        suffix: str,
        padding: int,
        start_index: int,
    ) -> None:
        super().__init__()
        self.logger = get_tool_logger("folder_creator")
        self.parent_path = parent_path
        self.count = count
        self.prefix = prefix
        self.suffix = suffix
        self.padding = padding
        self.start_index = start_index

    @Slot()
    def run(self) -> None:
        """작업 실행"""
        try:
            self.logger.info("Folder creation task started: parent=%s, count=%d, prefix=%s, suffix=%s", 
                           self.parent_path, self.count, self.prefix, self.suffix)
            
            if not self.parent_path.exists():
                self.logger.debug("Parent directory does not exist, will be created: %s", self.parent_path)
            
            # 초기 진행률 알림
            self.progress.emit(0, self.count)
            self.progressed.emit(f"Creating {self.count} folders in {self.parent_path}...\n")
            
            # 폴더 생성
            created_folders = create_folders(
                self.parent_path,
                self.count,
                self.prefix,
                self.suffix,
                self.padding,
                self.start_index,
            )
            
            # 진행률 업데이트
            for i, folder in enumerate(created_folders, 1):
                self.progress.emit(i, self.count)
                self.progressed.emit(f"Created: {folder.name}\n")
            
            self.logger.info("Task completed: %d folders created successfully", len(created_folders))
            self.finished.emit(len(created_folders))
        except Exception as e:  # noqa: BLE001
            self.logger.error("Task failed: %s", str(e), exc_info=True)
            self.failed.emit(str(e))


# CLI 테스트 지원
if __name__ == "__main__":
    import sys
    import argparse
    from PySide6.QtCore import QCoreApplication, QThread
    
    parser = argparse.ArgumentParser(description="Folder Creator Pipeline 테스트")
    parser.add_argument('--parent-path', type=str, required=True, help='부모 폴더 경로')
    parser.add_argument('--count', type=int, required=True, help='생성할 폴더 개수')
    parser.add_argument('--prefix', type=str, default='test', help='폴더명 prefix')
    parser.add_argument('--suffix', type=str, default='bseong', help='폴더명 suffix')
    parser.add_argument('--padding', type=int, default=4, help='숫자 패딩 너비')
    parser.add_argument('--start-index', type=int, default=1, help='시작 인덱스')
    
    args = parser.parse_args()
    
    parent_path = Path(args.parent_path)
    
    # QApplication 생성 (GUI 없이)
    app = QCoreApplication(sys.argv)
    
    # Worker 생성
    worker = FolderCreatorWorker(
        parent_path=parent_path,
        count=args.count,
        prefix=args.prefix,
        suffix=args.suffix,
        padding=args.padding,
        start_index=args.start_index,
    )
    
    # 시그널 연결
    def on_progressed(text: str):
        print(text, end='')
    
    def on_progress(current: int, total: int):
        print(f"\rProgress: {current}/{total} ({current*100//total if total > 0 else 0}%)", end='', flush=True)
    
    def on_finished(count: int):
        print(f"\nCompleted: {count} folders created")
        app.quit()
    
    def on_failed(msg: str):
        print(f"\nError: {msg}")
        app.quit()
    
    worker.progressed.connect(on_progressed)
    worker.progress.connect(on_progress)
    worker.finished.connect(on_finished)
    worker.failed.connect(on_failed)
    
    # Worker를 스레드에서 실행
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    thread.finished.connect(app.quit)
    thread.start()
    
    print(f"Task started: Creating {args.count} folders in {parent_path}")
    print("-" * 50)
    
    app.exec()
    
    thread.quit()
    thread.wait()
    
    print("-" * 50)
    print("Test completed")

