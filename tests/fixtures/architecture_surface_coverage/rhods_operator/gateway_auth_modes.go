package gateway

// Sanitized source shape for the three distinct gateway authentication modes.
func createAuthProxy(ctx context.Context, request *Request) error {
	mode, err := cluster.GetClusterAuthenticationMode(ctx, request.Client)
	if err != nil {
		return err
	}

	switch mode {
	case cluster.AuthModeOIDC:
		if request.Gateway.Spec.OIDC == nil {
			request.MarkNotReady("OIDC configuration is required")
			return nil
		}
		request.UseTemplate("kube-auth-proxy-oidc")
	case cluster.AuthModeIntegratedOAuth:
		request.UseTemplate("kube-auth-proxy-openshift")
	case cluster.AuthModeNone:
		request.MarkReady("external authentication; no gateway auth proxy")
		return nil
	}

	request.CreateAuthProxySecret()
	if mode == cluster.AuthModeIntegratedOAuth {
		request.CreateOAuthClient()
	}
	return nil
}
