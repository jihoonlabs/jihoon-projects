class InputBuffer:
    def __init__(self):
        # 최근 입력들을 저장하는 리스트 상하좌우 방향 버튼 2번 클릭으로 스킬 
        # 예: [("D", 100), ("D", 110), ("R", 130)]
        self.inputs = []

        # 마지막으로 성립한 커맨드 저장
        # 예: "DD", "RR", "LL", "UU"
        self.last_command = None

        # 마지막 커맨드가 몇 프레임에 성립했는지 저장
        self.last_command_frame = -999

    def push(self, key, frame):
        # 입력 하나를 버퍼에 추가
        # key  : "D", "L", "R", "U"
        # frame: 현재 프레임 번호
        self.inputs.append((key, frame))

        # 입력이 너무 많이 쌓이면 오래된 것부터 제거
        # 최근 입력만 남겨두기 위해 10개까지만 유지
        if len(self.inputs) > 10:
            self.inputs.pop(0)

        # 방금 넣은 key가 1초(20프레임) 안에 2번 눌렸는지 확인
        if self.check_double_tap(key, frame, window=20):
            # 예: key가 "D"면 "DD" 저장
            self.last_command = key + key

            # 이 커맨드가 성립한 프레임 기록
            self.last_command_frame = frame

    def check_double_tap(self, key, current_frame, window=20):
        # 같은 방향 입력이 최근 1초 안에 몇 번 있었는지 저장할 리스트
        matched_frames = []

        # 저장된 모든 입력을 하나씩 검사
        for input_key, input_frame in self.inputs:
            # 1) 입력 방향이 같은지 확인
            # 2) 현재 프레임 기준으로 window(20프레임 = 1초) 안인지 확인
            if input_key == key and current_frame - input_frame <= window:
                # 조건을 만족하면 그 입력의 프레임 기록
                matched_frames.append(input_frame)

        # 같은 방향 입력이 2번 이상 있으면 더블탭 성공
        return len(matched_frames) >= 2

    def get_command(self, current_frame, command_window=20):
        # 아직 성립한 커맨드가 없으면 None 반환
        if self.last_command is None:
            return None

        # 마지막 커맨드가 1초 안의 최신 커맨드면 반환
        # 예: "DD", "RR", "LL", "UU"
        if current_frame - self.last_command_frame <= command_window:
            return self.last_command

        # 시간이 너무 지나면 커맨드 무효 처리
        return None

    def clear_command(self):
        # 기술 발동 후 커맨드를 비워서
        # 같은 커맨드가 계속 재사용되지 않게 함
        self.last_command = None

        # 커맨드 프레임도 초기화
        self.last_command_frame = -999