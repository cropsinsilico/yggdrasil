#define _USE_MATH_DEFINES  // Required to use M_PI with MSVC
#include <math.h>
#include <stdio.h>
#include "YggInterface.hpp"


void timestep_calc(rapidjson::units::Quantity<double>& t,
		   rapidjson::Document& state, std::string model) {
  rapidjson::units::Quantity<double> x_period(10.0, "days");
  rapidjson::units::Quantity<double> y_period(5.0, "days");
  rapidjson::units::Quantity<double> z_period(10.0, "days");
  rapidjson::units::Quantity<double> o_period(2.5, "days");
#define SET_(key, val)				\
  if (!state.HasMember(key))			\
    state.AddMember(key, rapidjson::Value(val).Move(),	\
		    state.GetAllocator());		\
  else							\
    state[key].SetDouble(val)
  if (model == "A") {
    SET_("x", sin(2.0 * M_PI * (t / x_period).value()));
    SET_("y", cos(2.0 * M_PI * (t / y_period).value()));
    SET_("z1", -cos(2.0 * M_PI * (t / z_period).value()));
    SET_("z2", -cos(2.0 * M_PI * (t / z_period).value()));
    SET_("a", sin(2.0 * M_PI * (t / o_period).value()));
  } else {
    SET_("xvar", sin(2.0 * M_PI * (t / x_period).value()) / 2.0);
    SET_("yvar", cos(2.0 * M_PI * (t / y_period).value()));
    SET_("z", -2.0 * cos(2.0 * M_PI * (t / z_period).value()));
    SET_("b", cos(2.0 * M_PI * (t / o_period).value()));
  }
}


int main(int argc, char *argv[]) {

  char* t_units = argv[2];
  rapidjson::units::Quantity<double> t_step(atof(argv[1]), t_units);
  std::cout << "Hello from C++ timesync: timestep " << t_step << std::endl;
  rapidjson::units::Quantity<double> t_start(0.0, t_units);
  rapidjson::units::Quantity<double> t_end(5.0, "days");
  
  std::string model(argv[3]);
  int ret;
  rapidjson::Document state_send(rapidjson::kObjectType);
  rapidjson::Document state_recv(rapidjson::kObjectType);
  timestep_calc(t_start, state_send, model);

  // Set up connections matching yaml
  // Timestep synchronization connection will be 'statesync'
  YggTimesync timesync("statesync", t_units);
  dtype_t* out_dtype = create_dtype_json_object(0, NULL, NULL, true);
  YggOutput out("output", out_dtype);

  // Initialize state and synchronize with other models
  rapidjson::units::Quantity<double> t = t_start;
  ret = timesync.call(3, t.value(), &state_send, &state_recv);
  if (ret < 0) {
    std::cerr << "timesync(C++): Initial sync failed." << std::endl;
    return -1;
  }
  std::cout << "timesync(C++): t = " << t;
  for (rapidjson::Value::MemberIterator it = state_recv.MemberBegin();
       it != state_recv.MemberEnd(); it++)
    std::cout << ", " << it->name.GetString() <<
      " = " << it->value.GetDouble();
  std::cout << std::endl;

  // Send initial state to output
  rapidjson::Document msg;
  msg.CopyFrom(state_recv, msg.GetAllocator());
  msg.AddMember("time", rapidjson::Value(t).Move(), msg.GetAllocator());
  ret = out.send(1, &msg);
  if (ret < 0) {
    std::cerr << "timesync(C++): Failed to send initial output for t=" <<
      t << std::endl;
    return -1;
  }

  // Iterate until end
  while (t < t_end) {

    // Perform calculations to update the state
    t = t + t_step;
    timestep_calc(t, state_send, model);

    // Synchronize the state
    ret = timesync.call(3, t.value(), &state_send, &state_recv);
    if (ret < 0) {
      std::cerr << "timesync(C++): sync for t=" << t << " failed" << std::endl;
      return -1;
    }
    std::cout << "timesync(C++): t = " << t;
    for (rapidjson::Value::MemberIterator it = state_recv.MemberBegin();
	 it != state_recv.MemberEnd(); it++)
      std::cout << ", " << it->name.GetString() <<
	" = " << it->value.GetDouble();
    std::cout << std::endl;

    // Send output
    msg.CopyFrom(state_recv, msg.GetAllocator());
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
