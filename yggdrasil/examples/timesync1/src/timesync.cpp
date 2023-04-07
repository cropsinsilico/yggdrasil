#define _USE_MATH_DEFINES  // Required to use M_PI with MSVC
#include <math.h>
#include <stdio.h>
#include "YggInterface.hpp"


void timestep_calc(rapidjson::units::Quantity<double>& t,
		  rapidjson::Document& state) {
  rapidjson::units::Quantity<double> x_period(10.0, "days");
  rapidjson::units::Quantity<double> y_period(5.0, "days");
  double x = sin(2.0 * M_PI * (t / x_period).value());
  double y = cos(2.0 * M_PI * (t / y_period).value());
#define SET_(key, val)					\
  if (!state.HasMember(key))				\
    state.AddMember(key, rapidjson::Value(val).Move(),	\
		    state.GetAllocator());		\
  else							\
    state[key].SetDouble(val)
  SET_("x", x);
  SET_("y", y);
}


int main(int argc, char *argv[]) {

  char* t_units = argv[2];
  rapidjson::units::Quantity<double> t_step(atof(argv[1]), t_units);
  std::cout << "Hello from C++ timesync: timestep " << t_step << std::endl;
  rapidjson::units::Quantity<double> t_start(0.0, t_units);
  rapidjson::units::Quantity<double> t_end(5.0, "days");
  rapidjson::Document state(rapidjson::kObjectType);
  timestep_calc(t_start, state);
  int ret = 0;

  // Set up connections matching yaml
  // Timestep synchronization connection will default to 'timesync'
  YggTimesync timesync("timesync", t_units);
  dtype_t* out_dtype = create_dtype_json_object(0, NULL, NULL, true);
  YggOutput out("output", out_dtype);

  // Initialize state and synchronize with other models
  rapidjson::units::Quantity<double> t = t_start;
  ret = timesync.call(3, t.value(), &state, &state);
  if (ret < 0) {
    std::cerr << "timesync(C++): Initial sync failed." << std::endl;
    return -1;
  }
  std::cout << "timesync(C++): t = " << t <<
    ", x = " << state["x"].GetDouble() <<
    ", y = " << state["x"].GetDouble() << std::endl;

  // Send initial state to output
  rapidjson::Document msg;
  msg.CopyFrom(state, msg.GetAllocator());
  msg.AddMember("time", rapidjson::Value(t).Move(), msg.GetAllocator());
  ret = out.send(1, &msg);
  if (ret < 0) {
    std::cerr << "timesync(C++): Failed to send initial output for t=" << t << std::endl;
    return -1;
  }

  // Iterate until end
  while (t < t_end) {

    // Perform calculations to update the state
    t = t + t_step;
    timestep_calc(t, state);

    // Synchronize the state
    ret = timesync.call(3, t.value(), &state, &state);
    if (ret < 0) {
      std::cerr << "timesync(C++): sync for t=" << t << " failed" << std::endl;
      return -1;
    }
    std::cout << "timesync(C++): t = " << t <<
      ", x = " << state["x"].GetDouble() <<
      ", y = " << state["x"].GetDouble() << std::endl;

    // Send output
    msg.CopyFrom(state, msg.GetAllocator());
    msg.AddMember("time", rapidjson::Value(t).Move(), msg.GetAllocator());
    ret = out.send(1, &msg);
    if (ret < 0) {
      std::cerr << "timesync(C++): Failed to send output for t=" << t << std::endl;
      return -1;
    }
  }

  std::cout << "Goodbye from C++ timesync" << std::endl;
  return 0;
    
}
