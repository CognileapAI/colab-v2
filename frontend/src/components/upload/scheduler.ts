// 동시성 제한 큐. 전역 4 — 호스트당 연결 6 에서 프리사인드 PUT 의
// 매번-프리플라이트와 우리 API 호출이 들어갈 여유를 남긴다.
// 멀티파트는 동시에 1개 — 큰 파일 하나가 큐 전체를 점유하지 않게.
// 근거: dev-package/PLAN-SoT.md §9 〈277〉

interface Waiting {
  multipart: boolean;
  start: () => void;
}

export class Scheduler {
  private running = 0;

  private multipartRunning = 0;

  private paused = false;

  private readonly queue: Waiting[] = [];

  constructor(
    private readonly maxConcurrent = 4,
    private readonly maxMultipart = 1,
  ) {}

  run<T>(task: () => Promise<T>, opts?: { multipart?: boolean }): Promise<T> {
    const multipart = opts?.multipart ?? false;
    return new Promise<T>((resolve, reject) => {
      const start = () => {
        this.running += 1;
        if (multipart) this.multipartRunning += 1;
        task().then(resolve, reject).finally(() => {
          this.running -= 1;
          if (multipart) this.multipartRunning -= 1;
          this.pump();
        });
      };
      this.queue.push({ multipart, start });
      this.pump();
    });
  }

  pause(): void {
    this.paused = true;
  }

  resume(): void {
    this.paused = false;
    this.pump();
  }

  private pump(): void {
    if (this.paused) return;
    for (let i = 0; i < this.queue.length; ) {
      if (this.running >= this.maxConcurrent) return;
      const item = this.queue[i];
      if (item === undefined) return;
      if (item.multipart && this.multipartRunning >= this.maxMultipart) {
        i += 1; // 멀티파트 자리가 없다 — 뒤의 단일 작업은 지나갈 수 있다
        continue;
      }
      this.queue.splice(i, 1);
      item.start();
    }
  }
}
