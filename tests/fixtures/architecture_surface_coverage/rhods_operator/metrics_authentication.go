package main

// Sanitized source shape for the controller-runtime metrics configuration.
func controllerOptions(oconfig operatorConfig, tlsOpts []tlsOption) ctrl.Options {
	return ctrl.Options{
		Metrics: func() ctrlmetrics.Options {
			opts := ctrlmetrics.Options{
				BindAddress:   oconfig.MetricsAddr,
				SecureServing: oconfig.MetricsSecure,
				TLSOpts:       tlsOpts,
			}
			if oconfig.MetricsSecure {
				opts.FilterProvider = filters.WithAuthenticationAndAuthorization
			}
			if oconfig.MetricsCertPath != "" {
				opts.CertDir = oconfig.MetricsCertPath
				opts.CertName = oconfig.MetricsCertName
				opts.KeyName = oconfig.MetricsCertKey
			}
			return opts
		}(),
	}
}
