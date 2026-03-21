# flow_forecast_service

阶段1实现内容：

- 默认模型：`LightGBMRegressor`
- 输入字段：`flow_m3s`, `rain_intensity_mmph`, `temp_C`
- 窗口长度：24（120 秒）
- 统一接口：`GET /health`、`GET /meta`、`POST /infer`
