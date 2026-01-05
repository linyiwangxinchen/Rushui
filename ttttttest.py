        # 时间序列输入
        thrust_layout.addWidget(QLabel("时间序列 (s):"), 0, 0)
        self.time_sequence_input = QLineEdit()
        self.time_sequence_input.setPlaceholderText("示例: 0, 0.5, 1.0, 1.5, 2.0")
        self.time_sequence_input.setText("0, 0.56, 0.57, 100")
        thrust_layout.addWidget(self.time_sequence_input, 0, 1)

        # 推力序列输入
        thrust_layout.addWidget(QLabel("推力序列 (N):"), 1, 0)
        self.thrust_sequence_input = QLineEdit()
        self.thrust_sequence_input.setPlaceholderText("示例: 25000, 22000, 18000, 15000, 7000")
        self.thrust_sequence_input.setText("25080.6, 25080.6, 6971.4, 6971.4")

        thrust_layout.addWidget(self.thrust_sequence_input, 1, 1)
